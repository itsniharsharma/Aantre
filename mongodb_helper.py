"""MongoDB helper for storing and managing downloaded songs"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from gridfs import GridFS
from datetime import datetime

load_dotenv()

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

            self.client = MongoClient(
                MONGO_URI,
                connectTimeoutMS=10000,
                serverSelectionTimeoutMS=10000,
                maxPoolSize=10,
                retryWrites=True,
                tls=True,
                tlsAllowInvalidCertificates=allow_invalid,
            )
            
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
    
    def store_song(self, filepath, artist, session_id=None, file_type=None, source_filename=None):
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
            
            if sid := (session_id or self.current_session_id):
                self.songs_collection.update_one(
                    {"_id": sid},
                    {"$push": {"song_ids": file_id}}
                )
            
            print(f"✅ Stored in MongoDB: {filename}")
            return file_id
            
        except Exception as e:
            print(f"⚠️ Failed to store song: {e}")
            return None
    
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
