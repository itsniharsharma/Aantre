"""MongoDB helper for storing and managing downloaded songs"""

import os
import sys
import ssl
from dotenv import load_dotenv
from pymongo import MongoClient
try:
    import certifi
except Exception:
    certifi = None
from gridfs import GridFS
from datetime import datetime

load_dotenv()

def _find_ca_file() -> str:
    env_path = os.getenv("MONGO_TLS_CA_FILE")
    if env_path and os.path.exists(env_path):
        return env_path

    if certifi:
        try:
            cert_path = certifi.where()
            if cert_path and os.path.exists(cert_path):
                return cert_path
        except Exception:
            pass

    # Fallback to common locations (conda/venv)
    py_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    candidates = [
        os.path.join(sys.prefix, "Lib", "site-packages", "certifi", "cacert.pem"),
        os.path.join(sys.prefix, "lib", py_version, "site-packages", "certifi", "cacert.pem"),
        os.path.join(os.getcwd(), ".conda", "Lib", "site-packages", "certifi", "cacert.pem"),
    ]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate

    return ""


def _build_ssl_context(ca_file: str, allow_invalid: bool):
    try:
        context = ssl.create_default_context(cafile=ca_file or None)
        if hasattr(ssl, "TLSVersion"):
            context.minimum_version = ssl.TLSVersion.TLSv1_2
        if allow_invalid:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        return context
    except Exception:
        return None

class MongoDBHandler:
    """Optimized MongoDB handler with lazy connection and batch operations"""
    
    def __init__(self):
        self.connected = False
        self.client = None
        self.db = None
        self.fs = None
        self.songs_collection = None
        self.current_session_id = None
        self._connect()
    
    def _connect(self):
        """Establish MongoDB connection with optimized settings"""
        try:
            MONGO_URI = os.getenv("MONGO_URI")
            if not MONGO_URI:
                print("⚠️ MONGO_URI not found in .env")
                return
                
            allow_invalid = os.getenv("MONGO_TLS_INSECURE", "0") == "1"
            ca_file = _find_ca_file()

            ssl_context = _build_ssl_context(ca_file, allow_invalid)

            client_kwargs = {
                "connectTimeoutMS": 10000,
                "serverSelectionTimeoutMS": 10000,
                "maxPoolSize": 10,
                "retryWrites": True,
                "tls": True,
                "tlsAllowInvalidCertificates": allow_invalid,
            }
            if ssl_context:
                client_kwargs["ssl_context"] = ssl_context
                if ca_file:
                    print(f"✅ MongoDB TLS CA loaded: {ca_file}")
                else:
                    print("⚠️ MongoDB TLS CA not found; using default SSL context.")
            elif ca_file:
                client_kwargs["tlsCAFile"] = ca_file
                print(f"✅ MongoDB TLS CA loaded: {ca_file}")
            elif not allow_invalid:
                print("⚠️ MongoDB TLS CA not found; set MONGO_TLS_CA_FILE if needed.")

            self.client = MongoClient(MONGO_URI, **client_kwargs)
            
            self.client.admin.command('ping')
            
            self.db = self.client['mashup']
            self.fs = GridFS(self.db)
            self.songs_collection = self.db['songs_metadata']
            self.connected = True
            print("✅ MongoDB connected successfully")
            
        except Exception as e:
            self.connected = False
            print(f"⚠️ MongoDB connection failed: {e}")
    
    def start_new_session(self, artist_name, user_email):
        """Start a new mashup generation session"""
        if not self.connected:
            return None
            
        try:
            result = self.songs_collection.insert_one({
                "artist": artist_name,
                "user_email": user_email,
                "started_at": datetime.utcnow(),
                "status": "processing",
                "song_ids": []
            })
            self.current_session_id = result.inserted_id
            print(f"✅ Started session: {self.current_session_id}")
            return self.current_session_id
        except Exception as e:
            print(f"⚠️ Failed to start session: {e}")
            return None
    
    def store_song(self, filepath, artist, session_id=None, file_type=None, source_filename=None, append_to_session=True):
        """Store a song in MongoDB GridFS with chunked upload"""
        if not self.connected or not os.path.exists(filepath):
            return None
            
        try:
            filename = os.path.basename(filepath)
            
            with open(filepath, 'rb') as f:
                file_id = self.fs.put(
                    f,
                    filename=filename,
                    artist=artist,
                    session_id=session_id or self.current_session_id,
                    uploaded_at=datetime.utcnow(),
                    file_type=file_type,
                    source_filename=source_filename,
                    chunk_size=261120
                )
            
            if append_to_session and (sid := (session_id or self.current_session_id)):
                self.songs_collection.update_one(
                    {"_id": sid},
                    {"$push": {"song_ids": file_id}}
                )
            
            print(f"✅ Stored in MongoDB: {filename}")
            return file_id
            
        except Exception as e:
            print(f"⚠️ Failed to store song: {e}")
            return None

    def append_session_songs(self, session_id, file_ids):
        """Append multiple song IDs to a session in one update."""
        if not self.connected or not session_id or not file_ids:
            return False

        try:
            self.songs_collection.update_one(
                {"_id": session_id},
                {"$push": {"song_ids": {"$each": list(file_ids)}}}
            )
            return True
        except Exception as e:
            print(f"⚠️ Failed to append session songs: {e}")
            return False
    
    def delete_session_songs(self, session_id=None):
        """Delete all songs for a given session with batch operations"""
        if not self.connected:
            return False
            
        try:
            sid = session_id or self.current_session_id
            if not sid:
                return False
            
            session = self.songs_collection.find_one({"_id": sid})
            if not session:
                print(f"⚠️ Session not found: {sid}")
                return False
            
            deleted_count = 0
            for song_id in session.get("song_ids", []):
                try:
                    self.fs.delete(song_id)
                    deleted_count += 1
                except:
                    pass
            
            self.songs_collection.update_one(
                {"_id": sid},
                {"$set": {
                    "status": "completed",
                    "completed_at": datetime.utcnow(),
                    "songs_deleted": True
                }}
            )
            
            print(f"✅ Deleted {deleted_count} songs from MongoDB")
            return True
            
        except Exception as e:
            print(f"⚠️ Failed to delete session songs: {e}")
            return False
    
    def get_session_stats(self):
        """Get statistics about current session"""
        if not self.connected or not self.current_session_id:
            return None
            
        try:
            session = self.songs_collection.find_one({"_id": self.current_session_id})
            return session and {
                "session_id": str(self.current_session_id),
                "artist": session.get("artist"),
                "songs_count": len(session.get("song_ids", [])),
                "status": session.get("status")
            }
        except Exception as e:
            print(f"⚠️ Failed to get session stats: {e}")
            return None

mongo_handler = MongoDBHandler()
