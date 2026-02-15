from flask import Flask, request, render_template_string, send_file, redirect, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import zipfile
import os
import subprocess
import sys
import threading
import secrets
import string
from time import sleep
from datetime import datetime
from dotenv import load_dotenv
from mashup_core import run_mashup, DOWNLOAD_DIR, TRIM_DIR
from mongodb_helper import mongo_handler

V2_DIR = os.path.join(os.path.dirname(__file__), "v-2-multimash")
if V2_DIR not in sys.path:
    sys.path.insert(0, V2_DIR)

from multimash_core import run_multi_mashup

load_dotenv()
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

STREAM_ROOM_MAX = 30
STREAM_CODE_LEN = 6
STREAM_COLLECTION = "stream_rooms"
_STREAM_INDEX_READY = False
STREAM_PARTICIPANTS = {}
SOCKET_ROOM_BY_SID = {}
STREAM_ROOMS_LOCAL = {}
STREAM_HOSTS = {}
LAST_CHAT_BY_SID = {}

HOME_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Aantre — Live Music Streaming</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Sora:wght@400;500;600;700&display=swap" rel="stylesheet">

<style>
:root {
    --black: #05060a;
    --black-2: #0b0e16;
    --black-3: #101625;
    --cyan: #3bd6c6;
    --cyan-2: #1aa397;
    --amber: #f1c27b;
    --white: #ffffff;
    --muted: #8f98ab;
    --blue: var(--cyan);
    --blue-2: var(--cyan-2);
    --blue-3: #7cf2e5;
}

* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: "Sora", Arial, sans-serif;
    color: var(--white);
    background: radial-gradient(1200px 600px at 20% -10%, #0f1a2a 0%, transparent 60%),
                radial-gradient(900px 500px at 90% 0%, #0d1b22 0%, transparent 60%),
                linear-gradient(180deg, #06080f 0%, #05060a 60%);
    -webkit-text-size-adjust: 100%;
}

a { color: inherit; text-decoration: none; }

.btn {
    border: none;
    padding: 12px 18px;
    border-radius: 999px;
    font-weight: 600;
    cursor: pointer;
    transition: 0.2s;
}

.btn-primary {
    background: linear-gradient(135deg, var(--blue), var(--blue-2));
    color: #041012;
}

.btn-outline {
    background: transparent;
    color: var(--white);
    border: 2px solid rgba(255, 255, 255, 0.6);
}

.btn:hover { transform: translateY(-2px); }

.btn {
    border: none;
    padding: 12px 18px;
    border-radius: 999px;
    font-weight: 600;
    cursor: pointer;
    transition: 0.2s;
}

.btn-primary {
    background: linear-gradient(135deg, var(--cyan), var(--cyan-2));
    color: #041012;
}

.btn-outline {
    background: transparent;
    color: var(--white);
    border: 2px solid rgba(255, 255, 255, 0.6);
}

.btn:hover { transform: translateY(-2px); }

.btn {
    border: none;
    padding: 10px 16px;
    border-radius: 999px;
    font-weight: 600;
    cursor: pointer;
    transition: 0.2s;
}

.btn-primary {
    background: var(--blue);
    color: var(--white);
}

.btn-outline {
    background: transparent;
    color: var(--white);
    border: 2px solid var(--white);
}

.btn:hover { transform: translateY(-2px); }

.page {
    min-height: 100vh;
    position: relative;
    overflow-x: hidden;
}

.ribbon {
    position: absolute;
    top: -140px;
    right: -140px;
    width: 360px;
    height: 360px;
    background: radial-gradient(circle at 30% 30%, var(--cyan), var(--cyan-2));
    border-radius: 50%;
    opacity: 0.18;
}

.nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 22px 7vw;
    position: sticky;
    top: 0;
    background: rgba(11, 11, 11, 0.78);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid #232323;
    z-index: 10;
}

.logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: "Bebas Neue", "Sora", Arial, sans-serif;
    font-size: 26px;
    letter-spacing: 1px;
    color: var(--white);
}

.logo-mark {
    width: 34px;
    height: 34px;
    object-fit: contain;
    display: block;
}

.logo-text {
    letter-spacing: 1.2px;
}

.nav-links {
    display: flex;
    gap: 20px;
    font-weight: 600;
    color: var(--muted);
}

.nav-actions {
    display: flex;
    gap: 10px;
    align-items: center;
}

.nav-actions .btn {
    padding: 10px 16px;
    font-size: 14px;
}

.nav-actions {
    display: flex;
    gap: 10px;
    align-items: center;
}

.nav-actions .btn {
    padding: 10px 16px;
    font-size: 14px;
}

.nav-actions {
    display: flex;
    gap: 10px;
    align-items: center;
}

.nav-actions .btn {
    padding: 10px 16px;
    font-size: 14px;
}

.nav-actions {
    display: flex;
    gap: 10px;
    align-items: center;
}

.nav-actions .btn {
    padding: 10px 16px;
    font-size: 14px;
}

.nav-actions {
    display: flex;
    gap: 10px;
    align-items: center;
}

.nav-actions .btn {
    padding: 10px 16px;
    font-size: 14px;
}

.nav-actions {
    display: flex;
    gap: 10px;
    align-items: center;
}

.nav-actions .btn {
    padding: 10px 16px;
    font-size: 14px;
}

.nav-actions {
    display: flex;
    gap: 10px;
    align-items: center;
}

.nav-actions .btn {
    padding: 10px 16px;
    font-size: 14px;
}

.nav-links a {
    padding: 8px 12px;
    border-radius: 999px;
    transition: 0.2s;
}

.nav-links a:hover {
    background: var(--black-3);
    color: var(--white);
}

.headline {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    margin-bottom: 18px;
}

.headline h1 {
    font-family: "Bebas Neue", "Sora", Arial, sans-serif;
    font-size: 64px;
    line-height: 1.05;
    margin: 0 0 10px;
    color: var(--white);
}

.headline p {
    font-size: 18px;
    max-width: 620px;
    color: var(--muted);
    margin: 0;
}

.badge {
    padding: 10px 16px;
    border-radius: 999px;
    border: 1px solid #2a2a2a;
    background: rgba(30, 144, 255, 0.16);
    color: var(--blue-3);
    font-weight: 600;
    white-space: nowrap;
}

.toggle-group {
    display: inline-flex;
    gap: 8px;
    padding: 6px;
    border-radius: 999px;
    background: var(--black-3);
    margin-bottom: 16px;
}

.toggle-group button {
    border: none;
    padding: 8px 14px;
    border-radius: 999px;
    font-weight: 600;
    cursor: pointer;
    background: transparent;
    color: var(--muted);
}

.toggle-group button.active {
    background: var(--blue);
    color: var(--white);
}

.input-rows {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 10px;
}

.input-row {
    display: flex;
    gap: 10px;
}

.input-row input {
    margin-bottom: 0;
}

.btn-ghost {
    background: transparent;
    border: 1px solid #2a2a2a;
    color: var(--white);
}

.image-carousel {
    position: relative;
    width: 100%;
    max-width: 1200px;
    margin: 0 auto 40px;
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
}

.carousel-container {
    position: relative;
    height: 380px;
}

.carousel-slide {
    position: absolute;
    width: 100%;
    height: 100%;
    opacity: 0;
    transition: opacity 0.8s ease-in-out;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
}

.carousel-slide.active {
    opacity: 1;
}

.slide-content h2 {
    font-family: "Space Grotesk", Arial, sans-serif;
    font-size: 42px;
    margin: 0 0 12px;
    color: var(--white);
}

.slide-content p {
    font-size: 20px;
    color: rgba(255, 255, 255, 0.9);
    margin: 0;
}

.carousel-btn {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    background: rgba(0, 0, 0, 0.5);
    color: var(--white);
    border: none;
    padding: 16px;
    cursor: pointer;
    font-size: 18px;
    z-index: 10;
    transition: 0.3s;
}

.carousel-btn:hover {
    background: rgba(0, 0, 0, 0.8);
}

.carousel-btn.prev {
    left: 10px;
}

.carousel-btn.next {
    right: 10px;
}

.carousel-dots {
    position: absolute;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 10px;
    z-index: 10;
}

.dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.5);
    cursor: pointer;
    transition: 0.3s;
}

.dot.active {
    background: var(--blue);
    width: 32px;
    border-radius: 6px;
}

@media (max-width: 768px) {
    .carousel-container {
        height: 260px;
    }
    
    .slide-content h2 {
        font-size: 28px;
    }
    
    .slide-content p {
        font-size: 16px;
    }
}

.section {
    padding: 40px 7vw 10px;
}

.section h2 {
    font-family: "Space Grotesk", Arial, sans-serif;
    font-size: 36px;
    margin: 0 0 12px;
    color: var(--white);
}

.carousel-wrap {
    overflow: hidden;
    border: 1px solid #262626;
    border-radius: 22px;
    background: var(--black-2);
    padding: 18px 0;
    box-shadow: 0 16px 30px rgba(0, 0, 0, 0.4);
}

.carousel-track {
    display: flex;
    gap: 18px;
    width: max-content;
    padding: 6px 18px;
    animation: scroll 32s linear infinite;
}

.singer-card {
    display: flex;
    align-items: center;
    gap: 14px;
    min-width: 220px;
    padding: 16px 18px;
    border-radius: 16px;
    border: 1px solid #2c2c2c;
    background: var(--black-3);
}

.singer-card h3 {
    margin: 0 0 4px;
    font-size: 18px;
}

.singer-card span {
    font-size: 13px;
    color: var(--muted);
}

.cards {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 18px;
}

.card {
    background: var(--black-2);
    border: 1px solid #262626;
    border-radius: 18px;
    padding: 20px;
    box-shadow: 0 10px 26px rgba(0, 0, 0, 0.35);
}

.card h3 {
    margin: 0 0 8px;
    color: var(--white);
}

.form-wrap {
    background: var(--black-2);
    border: 1px solid #262626;
    border-radius: 22px;
    padding: 28px;
    box-shadow: 0 16px 36px rgba(0, 0, 0, 0.5);
}

label {
    font-size: 14px;
    font-weight: 600;
    color: var(--muted);
}

input {
    width: 100%;
    padding: 14px;
    margin-top: 6px;
    margin-bottom: 16px;
    border-radius: 12px;
    border: 1px solid #2a2a2a;
    outline: none;
    font-size: 16px;
    background: var(--black-3);
    color: var(--white);
}

.note {
    font-size: 12px;
    color: var(--muted);
    margin-top: -10px;
    margin-bottom: 12px;
}

.success,
.error {
    padding: 12px;
    border-radius: 12px;
    margin-bottom: 14px;
    color: var(--black);
    background: var(--blue);
}

.loader {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(11, 11, 11, 0.96);
    z-index: 9999;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: var(--white);
    padding: 20px;
}

.loader-message {
    max-width: 520px;
}

.loader-message h3 {
    font-size: 32px;
    margin: 0 0 10px;
    font-family: "Space Grotesk", Arial, sans-serif;
}

.loader-message p {
    color: var(--muted);
    font-size: 16px;
    margin: 6px 0;
}

.loader-spinner {
    width: 64px;
    height: 64px;
    margin: 0 auto 18px;
    border-radius: 50%;
    border: 5px solid rgba(255, 255, 255, 0.15);
    border-top-color: var(--blue);
    border-right-color: var(--blue-3);
    animation: spin 0.9s linear infinite;
}

.footer {
    border-top: 1px solid #232323;
    padding: 34px 7vw 36px;
    color: var(--muted);
    font-size: 13px;
}

.footer-grid {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr;
    gap: 24px;
    margin-bottom: 18px;
}

.footer h4 {
    margin: 0 0 10px;
    color: var(--white);
}

.footer a {
    color: var(--muted);
}

.footer-bottom {
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
}

.coming-soon {
    border: 1px dashed #2e2e2e;
    border-radius: 18px;
    padding: 18px 22px;
    background: rgba(30, 144, 255, 0.08);
    color: var(--blue-3);
    font-weight: 600;
}

@media (max-width: 980px) {
    .headline { flex-direction: column; align-items: flex-start; }
    .cards { grid-template-columns: 1fr; }
    .footer-grid { grid-template-columns: 1fr; }
}

@media (max-width: 640px) {
    .headline h1 { font-size: 42px; }
    .nav { flex-direction: column; gap: 10px; }
    .nav-links { flex-wrap: wrap; justify-content: center; }
    .nav-actions { flex-wrap: wrap; justify-content: center; }
    .section { padding: 28px 6vw 8px; }
    .carousel-wrap { border-radius: 16px; }
    .singer-card { min-width: 200px; padding: 12px 14px; }
    .form-wrap { padding: 22px; }
    .btn { width: 100%; padding: 14px 18px; }
    .badge { font-size: 12px; padding: 8px 12px; }
    .loader-message h3 { font-size: 26px; }
    .loader-message p { font-size: 14px; }
    .nav-links a { padding: 10px 14px; }
}

@media (max-width: 480px) {
    .headline h1 { font-size: 36px; }
    .headline p { font-size: 16px; }
    .section h2 { font-size: 28px; }
    .card { padding: 18px; }
    .footer { padding: 28px 6vw 32px; }
}

@media (prefers-reduced-motion: reduce) {
    .carousel-track { animation: none; }
}

@keyframes reveal {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes scroll {
    from { transform: translateX(0); }
    to { transform: translateX(-50%); }
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.section, .form-wrap { animation: reveal 0.6s ease both; }
</style>

<script>
function showLoader(message){
    if (message) {
        document.getElementById("loader-title").textContent = message;
    }
    document.getElementById("loader").style.display = "flex";
}

function syncLoaderState(){
    var loader = document.getElementById("loader");
    if (!loader) {
        return;
    }
    loader.style.display = "none";
}

window.addEventListener("load", syncLoaderState);

function setMultiMode(mode){
    var singerBtn = document.getElementById("mode-singer");
    var songBtn = document.getElementById("mode-song");
    var modeInput = document.getElementById("multi-mode");
    var videosWrap = document.getElementById("multi-videos-wrap");
    var videosInput = document.getElementById("multi-videos");
    var label = document.getElementById("multi-label");

    if (!modeInput || !singerBtn || !songBtn || !videosWrap || !label || !videosInput) {
        return;
    }

    modeInput.value = mode;
    singerBtn.classList.toggle("active", mode === "singer");
    songBtn.classList.toggle("active", mode === "song");
    videosWrap.style.display = mode === "song" ? "none" : "block";
    videosInput.required = mode === "singer";
    videosInput.disabled = mode === "song";
    label.textContent = mode === "song" ? "Songs (up to 5)" : "Singers (up to 5)";
    updatePlaceholders(mode);
}

function updatePlaceholders(mode){
    var inputs = document.querySelectorAll("#multi-inputs input[name='queries']");
    var prefix = mode === "song" ? "Song" : "Singer";
    for (var i = 0; i < inputs.length; i += 1) {
        inputs[i].placeholder = prefix + " " + (i + 1);
    }
}

function addMultiInput(){
    var container = document.getElementById("multi-inputs");
    if (!container) {
        return;
    }
    var count = container.querySelectorAll("input[name='queries']").length;
    if (count >= 5) {
        return;
    }

    var row = document.createElement("div");
    row.className = "input-row";

    var input = document.createElement("input");
    input.name = "queries";
    input.required = false;

    var modeInput = document.getElementById("multi-mode");
    var mode = modeInput ? modeInput.value : "singer";
    input.placeholder = (mode === "song" ? "Song " : "Singer ") + (count + 1);

    var removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "btn btn-ghost";
    removeBtn.textContent = "Remove";
    removeBtn.onclick = function(){
        container.removeChild(row);
        updatePlaceholders(mode);
    };

    row.appendChild(input);
    row.appendChild(removeBtn);
    container.appendChild(row);
}

window.addEventListener("load", function(){
    setMultiMode("singer");
});

var currentSlideIndex = 0;
var slideTimer;

function showSlide(n) {
    var slides = document.querySelectorAll('.carousel-slide');
    var dots = document.querySelectorAll('.dot');
    
    if (!slides.length) return;
    
    if (n >= slides.length) currentSlideIndex = 0;
    if (n < 0) currentSlideIndex = slides.length - 1;
    
    slides.forEach(function(slide) {
        slide.classList.remove('active');
    });
    
    dots.forEach(function(dot) {
        dot.classList.remove('active');
    });
    
    slides[currentSlideIndex].classList.add('active');
    dots[currentSlideIndex].classList.add('active');
}

function moveCarousel(n) {
    clearInterval(slideTimer);
    currentSlideIndex += n;
    showSlide(currentSlideIndex);
    startAutoSlide();
}

function currentSlide(n) {
    clearInterval(slideTimer);
    currentSlideIndex = n;
    showSlide(currentSlideIndex);
    startAutoSlide();
}

function startAutoSlide() {
    slideTimer = setInterval(function() {
        currentSlideIndex++;
        showSlide(currentSlideIndex);
    }, 5000);
}

function createStream(){
    fetch("/stream/create", { method: "POST" })
        .then(function(response){ return response.json(); })
        .then(function(data){
            if (data && data.ok && data.room_url) {
                window.location = data.room_url;
                return;
            }
            alert((data && data.error) ? data.error : "Could not create stream.");
        })
        .catch(function(){
            alert("Could not create stream.");
        });
}

function joinStream(){
    var code = prompt("Enter stream code");
    if (!code) {
        return;
    }
    code = code.trim().toUpperCase();
    if (!code) {
        return;
    }
    window.location = "/stream/" + encodeURIComponent(code);
}

window.addEventListener("load", function() {
    showSlide(currentSlideIndex);
    startAutoSlide();
});
</script>

</head>

<body data-ok="{{ 1 if ok_any else 0 }}">
<div class="page">
    <div class="ribbon"></div>

    <div class="nav">
        <div class="logo">
            <img class="logo-mark" src="/static/logo.png" alt="Aantre logo" onerror="this.style.display='none'">
            <span class="logo-text">AANTRE</span>
        </div>
        <div class="nav-links">
            <a href="/pricing">Plans</a>
            <a href="/#generate">Mashup Studio</a>
            <a href="/about">About</a>
        </div>
        <div class="nav-actions">
            <button class="btn btn-primary" type="button" onclick="createStream()">Create Stream</button>
            <button class="btn btn-outline" type="button" onclick="joinStream()">Join Stream</button>
        </div>
    </div>

    <section class="section" id="hero-carousel">
        <div class="image-carousel">
            <div class="carousel-container">
                <div class="carousel-slide active" style="background: linear-gradient(135deg, #1aa397 0%, #3bd6c6 100%);">
                    <div class="slide-content">
                        <h2>Live Rooms, Zero Friction</h2>
                        <p>Create a stream code and invite your audience instantly</p>
                    </div>
                </div>
                <div class="carousel-slide" style="background: linear-gradient(135deg, #0e2b3b 0%, #1aa397 100%);">
                    <div class="slide-content">
                        <h2>Premium Audio + Video</h2>
                        <p>Pro tuning for crisp sound and smooth playback</p>
                    </div>
                </div>
                <div class="carousel-slide" style="background: linear-gradient(135deg, #1a1f2f 0%, #3bd6c6 100%);">
                    <div class="slide-content">
                        <h2>Mashup Studio Included</h2>
                        <p>Generate professional mashups alongside live streams</p>
                    </div>
                </div>
            </div>
            <button class="carousel-btn prev" onclick="moveCarousel(-1)">&#10094;</button>
            <button class="carousel-btn next" onclick="moveCarousel(1)">&#10095;</button>
            <div class="carousel-dots">
                <span class="dot active" onclick="currentSlide(0)"></span>
                <span class="dot" onclick="currentSlide(1)"></span>
                <span class="dot" onclick="currentSlide(2)"></span>
            </div>
        </div>
    </section>

    <section class="section" id="showcase">
        <div class="headline">
            <div>
                <h1>Hostel Se Live, Seedha Dil Tak.</h1>
                <p>Stream your talent at Thapar with premium live rooms, audience chat, and pro-grade audio/video. Mashup Studio stays built-in for creators.</p>
            </div>
            <div class="badge">Version 3 — Live Streaming</div>
        </div>
        <h2>Stream Your Live Music Experience</h2>
        <div class="carousel-wrap" aria-label="Bollywood singers carousel">
            <div class="carousel-track">
                <div class="singer-card">
                    <div>
                        <h3>Arijit Singh</h3>
                        <span>Romantic ballads</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Shreya Ghoshal</h3>
                        <span>Classical fusion</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Sonu Nigam</h3>
                        <span>Evergreen hits</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Sunidhi Chauhan</h3>
                        <span>Power vocals</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Atif Aslam</h3>
                        <span>Signature timbre</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Neha Kakkar</h3>
                        <span>Dance anthems</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Armaan Malik</h3>
                        <span>Soft pop tone</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Kishore Kumar</h3>
                        <span>Legendary classics</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Lata Mangeshkar</h3>
                        <span>Golden era icon</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Asha Bhosle</h3>
                        <span>Timeless versatility</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Mohammed Rafi</h3>
                        <span>Classic melodies</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Mukesh</h3>
                        <span>Golden voice</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Udit Narayan</h3>
                        <span>90s romance</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Kumar Sanu</h3>
                        <span>90s chart hits</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Alka Yagnik</h3>
                        <span>Melodic charm</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>S. P. Balasubrahmanyam</h3>
                        <span>Pan-India legend</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Shaan</h3>
                        <span>Feel-good pop</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>KK</h3>
                        <span>Soulful hits</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Mohit Chauhan</h3>
                        <span>Indie romance</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Jubin Nautiyal</h3>
                        <span>Modern ballads</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Badshah</h3>
                        <span>Hip-hop hooks</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Honey Singh</h3>
                        <span>Party anthems</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Diljit Dosanjh</h3>
                        <span>Punjabi crossover</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Mika Singh</h3>
                        <span>High energy hits</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Vishal Dadlani</h3>
                        <span>Rock edge</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Shekhar Ravjiani</h3>
                        <span>Smooth hooks</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Shankar Mahadevan</h3>
                        <span>Carnatic power</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Hariharan</h3>
                        <span>Ghazi gharana</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Sukhwinder Singh</h3>
                        <span>Stage fire</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Javed Ali</h3>
                        <span>Romantic tone</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Kailash Kher</h3>
                        <span>Sufi soul</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Rahat Fateh Ali Khan</h3>
                        <span>Qawwali depth</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Nusrat Fateh Ali Khan</h3>
                        <span>Qawwali master</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Benny Dayal</h3>
                        <span>Groove pop</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Neeti Mohan</h3>
                        <span>Modern shine</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Shilpa Rao</h3>
                        <span>Sultry tone</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Monali Thakur</h3>
                        <span>Soft pop</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Palak Muchhal</h3>
                        <span>Love songs</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Tulsi Kumar</h3>
                        <span>Pop romance</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Kanika Kapoor</h3>
                        <span>Dance sparkle</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Dhvani Bhanushali</h3>
                        <span>Youth pop</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Jonita Gandhi</h3>
                        <span>Fresh vocals</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Asees Kaur</h3>
                        <span>Warm tone</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>B Praak</h3>
                        <span>Emotive power</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Arko</h3>
                        <span>Indie mood</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Ankit Tiwari</h3>
                        <span>Dark romance</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Darshan Raval</h3>
                        <span>Pop ballads</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Gajendra Verma</h3>
                        <span>Indie love</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Lucky Ali</h3>
                        <span>Acoustic soul</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Adnan Sami</h3>
                        <span>Piano melodies</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Abhijeet Bhattacharya</h3>
                        <span>Bollywood hits</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Kavita Krishnamurthy</h3>
                        <span>Classic elegance</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Sadhana Sargam</h3>
                        <span>Smooth melodies</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Mahalakshmi Iyer</h3>
                        <span>Silky vocals</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Roop Kumar Rathod</h3>
                        <span>Ghazal touch</span>
                    </div>
                </div>
                <div class="singer-card">
                    <div>
                        <h3>Nooran Sisters</h3>
                        <span>Folk power</span>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <section class="section" id="generate">
        <h2>Mashup Studio</h2>
        <div class="form-wrap">
            {% if msg_single %}
            <div class="{{'success' if ok_single else 'error'}}">{{msg_single}}</div>
            {% endif %}

            <form method="post" onsubmit="showLoader('Generating your mashup...')">
                <input type="hidden" name="form_type" value="single">
                <label>Singer / Artist Name</label>
                <input name="singer" required placeholder="e.g. Arijit Singh">

                <label>Number of Videos</label>
                <input name="n" type="number" required min="11">
                <div class="note">Must be greater than 10</div>

                <label>Clip Duration (seconds)</label>
                <input name="dur" type="number" required min="21">
                <div class="note">Must be greater than 20 seconds</div>

                <label>Email Address</label>
                <input name="email" type="email" required placeholder="you@gmail.com">

                <button class="btn btn-primary" type="submit">Generate Mashup</button>

                <div id="loader" class="loader">
                    <div class="loader-message">
                        <div class="loader-spinner" aria-hidden="true"></div>
                        <h3 id="loader-title">Your mashup is generating</h3>
                        <p>Kindly have patience and check your mail.</p>
                    </div>
                </div>
            </form>
        </div>
    </section>

    <section class="section" id="generate-multi">
        <h2>Premium Mashup Lab</h2>
        <div class="form-wrap">
            {% if msg_multi %}
            <div class="{{'success' if ok_multi else 'error'}}">{{msg_multi}}</div>
            {% endif %}

            <form method="post" onsubmit="showLoader('Generating your multi mashup...')">
                <input type="hidden" name="form_type" value="multi">
                <input type="hidden" id="multi-mode" name="multi_mode" value="singer">

                <div class="toggle-group" role="group" aria-label="Multi mashup mode">
                    <button type="button" id="mode-singer" class="active" onclick="setMultiMode('singer')">Singer</button>
                    <button type="button" id="mode-song" onclick="setMultiMode('song')">Song</button>
                </div>

                <label id="multi-label">Singers (up to 5)</label>
                <div id="multi-inputs" class="input-rows">
                    <div class="input-row">
                        <input name="queries" placeholder="Singer 1">
                        <button class="btn btn-ghost" type="button" onclick="addMultiInput()">Add</button>
                    </div>
                </div>
                <div class="note">Add only what you need. Maximum 5 entries.</div>

                <div id="multi-videos-wrap">
                    <label>Total Videos (shared across entries)</label>
                    <input id="multi-videos" name="n_multi" type="number" required min="10">
                    <div class="note">We split the total across your entries for balanced variety.</div>
                </div>

                <label>Clip Duration (seconds)</label>
                <input name="dur_multi" type="number" required min="21">
                <div class="note">Must be greater than 20 seconds</div>

                <label>Email Address</label>
                <input name="email_multi" type="email" required placeholder="you@gmail.com">

                <button class="btn btn-primary" type="submit">Generate Premium Mashup</button>
            </form>
        </div>
    </section>

    <section class="section" id="features">
        <h2>Core Streaming Features</h2>
        <div class="cards">
            <div class="card">
                <h3>Live Rooms</h3>
                <p>Create a unique code, invite viewers, and go live instantly.</p>
            </div>
            <div class="card">
                <h3>Audience Chat</h3>
                <p>Real-time chat keeps your community close to the performance.</p>
            </div>
            <div class="card">
                <h3>Premium Playback</h3>
                <p>High-fidelity audio/video tuning for smooth, crisp streams.</p>
            </div>
        </div>
    </section>

    <section class="section" id="coming-soon">
        <h2>Creator Hardware (Coming Soon)</h2>
        <div class="coming-soon">Pair Aantre ingestion devices via QR and broadcast studio-grade audio from your room.</div>
    </section>

    <footer class="footer">
        <div class="footer-grid">
            <div>
                <h4>Aantre</h4>
                <p>Bollywood mashups, clean trims, and instant delivery in a single experience.</p>
            </div>
            <div>
                <h4>Product</h4>
                <p><a href="/pricing">Pricing</a></p>
                <p><a href="/#generate">Generate</a></p>
                <p><a href="/about">About</a></p>
            </div>
            <div>
                <h4>Connect</h4>
                <p><a href="https://www.linkedin.com/in/itsniharsharma/" target="_blank" rel="noopener">LinkedIn</a></p>
            </div>
        </div>
        <div class="footer-bottom">
            <span>© 2026 Aantre. All rights reserved.</span>
            <span>Built with version 1 workflow.</span>
        </div>
    </footer>
</div>
</body>
</html>
"""

PRICING_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Aantre — Plans</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Sora:wght@400;500;600;700&display=swap" rel="stylesheet">

<style>
:root {
    --black: #05060a;
    --black-2: #0b0e16;
    --black-3: #101625;
    --cyan: #3bd6c6;
    --cyan-2: #1aa397;
    --amber: #f1c27b;
    --white: #ffffff;
    --muted: #8f98ab;
    --blue: var(--cyan);
    --blue-2: var(--cyan-2);
    --blue-3: #7cf2e5;
}

* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: "Sora", Arial, sans-serif;
    color: var(--white);
    background: radial-gradient(1200px 600px at 20% -10%, #0f1a2a 0%, transparent 60%),
                radial-gradient(900px 500px at 90% 0%, #0d1b22 0%, transparent 60%),
                linear-gradient(180deg, #06080f 0%, #05060a 60%);
}

a { color: inherit; text-decoration: none; }

.btn {
    border: none;
    padding: 12px 18px;
    border-radius: 999px;
    font-weight: 600;
    cursor: pointer;
    transition: 0.2s;
}

.btn-primary {
    background: linear-gradient(135deg, var(--blue), var(--blue-2));
    color: #041012;
}

.btn-outline {
    background: transparent;
    color: var(--white);
    border: 2px solid rgba(255, 255, 255, 0.6);
}

.btn:hover { transform: translateY(-2px); }

.btn {
    border: none;
    padding: 12px 18px;
    border-radius: 999px;
    font-weight: 600;
    cursor: pointer;
    transition: 0.2s;
}

.btn-primary {
    background: linear-gradient(135deg, var(--blue), var(--blue-2));
    color: #041012;
}

.btn-outline {
    background: transparent;
    color: var(--white);
    border: 2px solid rgba(255, 255, 255, 0.6);
}

.btn:hover { transform: translateY(-2px); }

.btn {
    border: none;
    padding: 12px 18px;
    border-radius: 999px;
    font-weight: 600;
    cursor: pointer;
    transition: 0.2s;
}

.btn-primary {
    background: linear-gradient(135deg, var(--blue), var(--blue-2));
    color: #041012;
}

.btn-outline {
    background: transparent;
    color: var(--white);
    border: 2px solid rgba(255, 255, 255, 0.6);
}

.btn:hover { transform: translateY(-2px); }

.page {
    min-height: 100vh;
    position: relative;
    overflow-x: hidden;
}

.ribbon {
    position: absolute;
    top: -140px;
    right: -140px;
    width: 360px;
    height: 360px;
    background: radial-gradient(circle at 30% 30%, var(--blue), var(--blue-2));
    border-radius: 50%;
    opacity: 0.18;
}

.nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 22px 7vw;
    position: sticky;
    top: 0;
    background: rgba(11, 11, 11, 0.78);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid #232323;
    z-index: 10;
}

.logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: "Bebas Neue", "Sora", Arial, sans-serif;
    font-size: 26px;
    letter-spacing: 1px;
    color: var(--white);
}

.logo-mark {
    width: 34px;
    height: 34px;
    object-fit: contain;
    display: block;
}

.logo-text {
    letter-spacing: 1.2px;
}

.nav-links {
    display: flex;
    gap: 20px;
    font-weight: 600;
    color: var(--muted);
}

.nav-links a {
    padding: 8px 12px;
    border-radius: 999px;
    transition: 0.2s;
}

.nav-links a:hover {
    background: var(--black-3);
    color: var(--white);
}

.section {
    padding: 60px 7vw 10px;
}

.section h1 {
    font-family: "Space Grotesk", Arial, sans-serif;
    font-size: 48px;
    margin: 0 0 12px;
}

.pricing-card {
    border: 1px solid #2a2a2a;
    border-radius: 20px;
    padding: 24px;
    background: var(--black-2);
    max-width: 420px;
}

.pricing-card strong {
    font-size: 40px;
    color: var(--blue);
}

.pricing-card ul {
    padding-left: 18px;
    color: var(--muted);
}

.footer {
    border-top: 1px solid #232323;
    padding: 34px 7vw 36px;
    color: var(--muted);
    font-size: 13px;
}

.footer-bottom {
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
}

@media (max-width: 640px) {
    .nav { flex-direction: column; gap: 10px; }
    .nav-links { flex-wrap: wrap; justify-content: center; }
    .nav-actions { flex-wrap: wrap; justify-content: center; }
    .section h1 { font-size: 40px; }
}
</style>
</head>
<body>
<div class="page">
    <div class="ribbon"></div>
    <div class="nav">
        <div class="logo">
            <img class="logo-mark" src="/static/logo.png" alt="Aantre logo" onerror="this.style.display='none'">
            <span class="logo-text">AANTRE</span>
        </div>
        <div class="nav-links">
            <a href="/pricing">Plans</a>
            <a href="/#generate">Mashup Studio</a>
            <a href="/about">About</a>
        </div>
        <div class="nav-actions">
            <button class="btn btn-primary" type="button" onclick="createStream()">Create Stream</button>
            <button class="btn btn-outline" type="button" onclick="joinStream()">Join Stream</button>
        </div>
    </div>

    <section class="section">
        <h1>Plans</h1>
        <p>Creator-first pricing while we build the live music community at Thapar.</p>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; max-width: 1100px; margin: 0 auto;">
            <div class="pricing-card">
                <h2>Free</h2>
                <strong>INR 0</strong>
                <p>Everything you need to generate your first mashup.</p>
                <ul>
                    <li>Auto search and download</li>
                    <li>Clean trims and stitching</li>
                    <li>Email delivery</li>
                </ul>
            </div>
            
            <div class="pricing-card" style="position: relative; border: 2px solid var(--primary);">
                <div style="position: absolute; top: -14px; left: 50%; transform: translateX(-50%); background: linear-gradient(135deg, var(--primary), var(--accent)); color: white; padding: 4px 16px; border-radius: 12px; font-size: 12px; font-weight: 600; letter-spacing: 0.5px;">CURRENTLY FREE</div>
                <h2>Regular Plan</h2>
                <strong style="text-decoration: line-through; opacity: 0.5;">INR 10</strong>
                <strong style="font-size: 32px; color: var(--primary);">FREE</strong>
                <p>Advanced multi-mashup features with premium quality.</p>
                <ul>
                    <li>Up to 5 singers or songs</li>
                    <li>Beat-synced transitions</li>
                    <li>Professional EQ & compression</li>
                    <li>Rotating crossover mixing</li>
                    <li>-14 LUFS mastering</li>
                </ul>
            </div>

            <div class="pricing-card" style="position: relative; opacity: 0.75;">
                <div style="position: absolute; top: -14px; left: 50%; transform: translateX(-50%); background: #2a2a2a; color: var(--muted); padding: 4px 16px; border-radius: 12px; font-size: 12px; font-weight: 600; letter-spacing: 0.5px;">UNAVAILABLE</div>
                <h2>Create a Band</h2>
                <strong>INR 199 / month</strong>
                <p>For creators who want to stream original music and sell their voice.</p>
                <ul>
                    <li>Creator streaming profile</li>
                    <li>Voice marketplace listing</li>
                    <li>Band collaboration workspace</li>
                    <li>Royalty-ready exports</li>
                    <li>Audience link-in-bio page</li>
                </ul>
            </div>
        </div>
    </section>

    <footer class="footer">
        <div class="footer-bottom">
            <span>© 2026 Aantre. All rights reserved.</span>
            <span>Version 2 pricing — Premium features launching soon.</span>
        </div>
    </footer>
</div>
<script>
function createStream(){
    fetch("/stream/create", { method: "POST" })
        .then(function(response){ return response.json(); })
        .then(function(data){
            if (data && data.ok && data.room_url) {
                window.location = data.room_url;
                return;
            }
            alert((data && data.error) ? data.error : "Could not create stream.");
        })
        .catch(function(){
            alert("Could not create stream.");
        });
}

function joinStream(){
    var code = prompt("Enter stream code");
    if (!code) {
        return;
    }
    code = code.trim().toUpperCase();
    if (!code) {
        return;
    }
    window.location = "/stream/" + encodeURIComponent(code);
}
</script>
</body>
</html>
"""

ABOUT_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Aantre — About Aantre Live</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Sora:wght@400;500;600;700&display=swap" rel="stylesheet">

<style>
:root {
    --black: #05060a;
    --black-2: #0b0e16;
    --black-3: #101625;
    --cyan: #3bd6c6;
    --cyan-2: #1aa397;
    --amber: #f1c27b;
    --white: #ffffff;
    --muted: #8f98ab;
    --blue: var(--cyan);
    --blue-2: var(--cyan-2);
    --blue-3: #7cf2e5;
}

* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: "Sora", Arial, sans-serif;
    color: var(--white);
    background: radial-gradient(1200px 600px at 20% -10%, #0f1a2a 0%, transparent 60%),
                radial-gradient(900px 500px at 90% 0%, #0d1b22 0%, transparent 60%),
                linear-gradient(180deg, #06080f 0%, #05060a 60%);
}

a { color: inherit; text-decoration: none; }

.btn {
    border: none;
    padding: 12px 18px;
    border-radius: 999px;
    font-weight: 600;
    cursor: pointer;
    transition: 0.2s;
}

.btn-primary {
    background: linear-gradient(135deg, var(--blue), var(--blue-2));
    color: #041012;
}

.btn-outline {
    background: transparent;
    color: var(--white);
    border: 2px solid rgba(255, 255, 255, 0.6);
}

.btn:hover { transform: translateY(-2px); }

.btn {
    border: none;
    padding: 12px 18px;
    border-radius: 999px;
    font-weight: 600;
    cursor: pointer;
    transition: 0.2s;
}

.btn-primary {
    background: linear-gradient(135deg, var(--blue), var(--blue-2));
    color: #041012;
}

.btn-outline {
    background: transparent;
    color: var(--white);
    border: 2px solid rgba(255, 255, 255, 0.6);
}

.btn:hover { transform: translateY(-2px); }

.page {
    min-height: 100vh;
    position: relative;
    overflow-x: hidden;
}

.ribbon {
    position: absolute;
    top: -140px;
    right: -140px;
    width: 360px;
    height: 360px;
    background: radial-gradient(circle at 30% 30%, var(--blue), var(--blue-2));
    border-radius: 50%;
    opacity: 0.18;
}

.nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 22px 7vw;
    position: sticky;
    top: 0;
    background: rgba(11, 11, 11, 0.78);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid #232323;
    z-index: 10;
}

.logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: "Bebas Neue", "Sora", Arial, sans-serif;
    font-size: 26px;
    letter-spacing: 1px;
    color: var(--white);
}

.logo-mark {
    width: 34px;
    height: 34px;
    object-fit: contain;
    display: block;
}

.logo-text {
    letter-spacing: 1.2px;
}

.nav-links {
    display: flex;
    gap: 20px;
    font-weight: 600;
    color: var(--muted);
}

.nav-links a {
    padding: 8px 12px;
    border-radius: 999px;
    transition: 0.2s;
}

.nav-links a:hover {
    background: var(--black-3);
    color: var(--white);
}

.section {
    padding: 60px 7vw 10px;
}

.section h1 {
    font-family: "Space Grotesk", Arial, sans-serif;
    font-size: 48px;
    margin: 0 0 12px;
}

.info-card {
    border: 1px solid #2a2a2a;
    border-radius: 20px;
    padding: 24px;
    background: var(--black-2);
}

.info-card ul {
    padding-left: 18px;
    color: var(--muted);
}

.footer {
    border-top: 1px solid #232323;
    padding: 34px 7vw 36px;
    color: var(--muted);
    font-size: 13px;
}

.footer-bottom {
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
}

@media (max-width: 640px) {
    .nav { flex-direction: column; gap: 10px; }
    .nav-links { flex-wrap: wrap; justify-content: center; }
    .nav-actions { flex-wrap: wrap; justify-content: center; }
    .section h1 { font-size: 40px; }
}
</style>
</head>
<body>
<div class="page">
    <div class="ribbon"></div>
    <div class="nav">
        <div class="logo">
            <img class="logo-mark" src="/static/logo.png" alt="Aantre logo" onerror="this.style.display='none'">
            <span class="logo-text">AANTRE</span>
        </div>
        <div class="nav-links">
            <a href="/pricing">Plans</a>
            <a href="/#generate">Mashup Studio</a>
            <a href="/about">About</a>
        </div>
        <div class="nav-actions">
            <button class="btn btn-primary" type="button" onclick="createStream()">Create Stream</button>
            <button class="btn btn-outline" type="button" onclick="joinStream()">Join Stream</button>
        </div>
    </div>

    <section class="section">
        <h1>About Aantre Live</h1>
        <div class="info-card">
            <p>Hi, I am Nihar Sharma. I am building Aantre as a software experience that helps people generate mashups quickly and cleanly.</p>
            <p>If you are interested in building your passion, let us team up and create something meaningful together.</p>
            <p>Connect on LinkedIn: <a href="https://www.linkedin.com/in/itsniharsharma/" target="_blank" rel="noopener" style="color: var(--blue-3); text-decoration: underline;">linkedin.com/in/itsniharsharma</a></p>
            
            <h3 style="margin-top: 32px;">Version 3 Features (Streaming)</h3>
            <ul>
                <li><strong>Live Rooms:</strong> Create a stream room with a unique code and invite anyone to join</li>
                <li><strong>Audience Chat:</strong> Viewers can chat live while watching the host stream</li>
                <li><strong>Host Broadcast Mode:</strong> Only the host streams audio/video for clean, stable sessions</li>
                <li><strong>Aantre Ingestion:</strong> Hardware or phone sources can be paired via QR for direct capture</li>
                <li><strong>Optimized Playback:</strong> Premium audio/video tuning for crisp, low-latency playback</li>
            </ul>

            <h3 style="margin-top: 32px;">Version 2 Features (Premium)</h3>
            <ul>
                <li><strong>Multi-Mashup Mode:</strong> Blend up to 5 singers or songs in one track</li>
                <li><strong>Beat-Synced Transitions:</strong> Smooth crossfades with tempo matching</li>
                <li><strong>Professional Audio Processing:</strong> Multi-band EQ, compression, and -14 LUFS mastering</li>
                <li><strong>Rotating Crossover Mixing:</strong> Dynamic A→B→A rotation pattern for engaging flow</li>
                <li><strong>Loudest-Window Selection:</strong> Automatically extracts the "antara" (most epic) sections</li>
            </ul>
            
            <h3 style="margin-top: 28px;">Version 1 Features (Free)</h3>
            <ul>
                <li>Smart search for top artist tracks</li>
                <li>Clean trims and seamless stitching</li>
                <li>Zip packaging and email delivery</li>
            </ul>
        </div>
    </section>

    <footer class="footer">
        <div class="footer-bottom">
            <span>© 2026 Aantre. All rights reserved.</span>
            <span>Built by Nihar Sharma.</span>
        </div>
    </footer>
</div>
<script>
function createStream(){
    fetch("/stream/create", { method: "POST" })
        .then(function(response){ return response.json(); })
        .then(function(data){
            if (data && data.ok && data.room_url) {
                window.location = data.room_url;
                return;
            }
            alert((data && data.error) ? data.error : "Could not create stream.");
        })
        .catch(function(){
            alert("Could not create stream.");
        });
}

function joinStream(){
    var code = prompt("Enter stream code");
    if (!code) {
        return;
    }
    code = code.trim().toUpperCase();
    if (!code) {
        return;
    }
    window.location = "/stream/" + encodeURIComponent(code);
}
</script>
</body>
</html>
"""

def normalize_stream_code(code: str) -> str:
    if not code:
        return ""
    return "".join([c for c in code.strip().upper() if c.isalnum()])


def ensure_stream_indexes() -> None:
    global _STREAM_INDEX_READY
    if _STREAM_INDEX_READY:
        return
    if not mongo_handler.connected or not mongo_handler.db:
        return
    try:
        coll = mongo_handler.db[STREAM_COLLECTION]
        coll.create_index("code", unique=True)
        coll.create_index("created_at")
        _STREAM_INDEX_READY = True
    except Exception:
        _STREAM_INDEX_READY = False


def create_stream_room() -> str:
    ensure_stream_indexes()
    alphabet = string.ascii_uppercase + string.digits

    for _ in range(15):
        code = "".join(secrets.choice(alphabet) for _ in range(STREAM_CODE_LEN))

        if mongo_handler.connected and mongo_handler.db:
            try:
                mongo_handler.db[STREAM_COLLECTION].insert_one({
                    "code": code,
                    "created_at": datetime.utcnow(),
                    "last_active": datetime.utcnow(),
                    "active": True,
                    "max_size": STREAM_ROOM_MAX,
                })
                return code
            except Exception as e:
                if "duplicate" in str(e).lower():
                    continue
                raise
        else:
            if code in STREAM_ROOMS_LOCAL:
                continue
            STREAM_ROOMS_LOCAL[code] = {
                "code": code,
                "created_at": datetime.utcnow(),
                "last_active": datetime.utcnow(),
                "active": True,
                "max_size": STREAM_ROOM_MAX,
            }
            return code

    raise RuntimeError("Unable to create a unique stream code.")


def get_stream_room(code: str):
    normalized = normalize_stream_code(code)
    if not normalized:
        return None
    if mongo_handler.connected and mongo_handler.db:
        return mongo_handler.db[STREAM_COLLECTION].find_one({"code": normalized, "active": True})
    room = STREAM_ROOMS_LOCAL.get(normalized)
    return room if room and room.get("active") else None


def update_stream_status(code: str, active: bool) -> None:
    normalized = normalize_stream_code(code)
    if not normalized:
        return
    if mongo_handler.connected and mongo_handler.db:
        mongo_handler.db[STREAM_COLLECTION].update_one(
            {"code": normalized},
            {"$set": {"active": active, "last_active": datetime.utcnow()}},
        )
    elif normalized in STREAM_ROOMS_LOCAL:
        STREAM_ROOMS_LOCAL[normalized]["active"] = active
        STREAM_ROOMS_LOCAL[normalized]["last_active"] = datetime.utcnow()


def touch_stream_room(code: str) -> None:
    normalized = normalize_stream_code(code)
    if not normalized:
        return
    if mongo_handler.connected and mongo_handler.db:
        mongo_handler.db[STREAM_COLLECTION].update_one(
            {"code": normalized},
            {"$set": {"last_active": datetime.utcnow()}},
        )
    elif normalized in STREAM_ROOMS_LOCAL:
        STREAM_ROOMS_LOCAL[normalized]["last_active"] = datetime.utcnow()

STREAM_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Aantre — Live Stream</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Sora:wght@400;500;600;700&display=swap" rel="stylesheet">

<style>
:root {
    --black: #05060a;
    --black-2: #0b0e16;
    --black-3: #101625;
    --cyan: #3bd6c6;
    --cyan-2: #1aa397;
    --amber: #f1c27b;
    --white: #ffffff;
    --muted: #8f98ab;
    --blue: var(--cyan);
    --blue-2: var(--cyan-2);
    --blue-3: #7cf2e5;
}

* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: "Sora", Arial, sans-serif;
    color: var(--white);
    background: radial-gradient(1200px 600px at 20% -10%, #0f1a2a 0%, transparent 60%),
                radial-gradient(900px 500px at 90% 0%, #0d1b22 0%, transparent 60%),
                linear-gradient(180deg, #06080f 0%, #05060a 60%);
}

a { color: inherit; text-decoration: none; }

.btn {
    border: none;
    padding: 10px 16px;
    border-radius: 999px;
    font-weight: 600;
    cursor: pointer;
    transition: 0.2s;
}

.btn-primary {
    background: var(--blue);
    color: var(--white);
}

.btn-outline {
    background: transparent;
    color: var(--white);
    border: 2px solid var(--white);
}

.btn-ghost {
    background: transparent;
    border: 1px solid #2a2a2a;
    color: var(--white);
}

.btn:hover { transform: translateY(-2px); }

.page {
    min-height: 100vh;
    position: relative;
    overflow-x: hidden;
}

.ribbon {
    position: absolute;
    top: -140px;
    right: -140px;
    width: 360px;
    height: 360px;
    background: radial-gradient(circle at 30% 30%, var(--blue), var(--blue-2));
    border-radius: 50%;
    opacity: 0.18;
}

.nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 22px 7vw;
    position: sticky;
    top: 0;
    background: rgba(11, 11, 11, 0.78);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid #232323;
    z-index: 10;
}

.logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: "Bebas Neue", "Sora", Arial, sans-serif;
    font-size: 26px;
    letter-spacing: 1px;
    color: var(--white);
}

.logo-mark {
    width: 34px;
    height: 34px;
    object-fit: contain;
    display: block;
}

.logo-text {
    letter-spacing: 1.2px;
}

.nav-links {
    display: flex;
    gap: 20px;
    font-weight: 600;
    color: var(--muted);
}

.nav-links a {
    padding: 8px 12px;
    border-radius: 999px;
    transition: 0.2s;
}

.nav-links a:hover {
    background: var(--black-3);
    color: var(--white);
}

.nav-actions {
    display: flex;
    gap: 10px;
    align-items: center;
}

.nav-actions .btn {
    padding: 10px 16px;
    font-size: 14px;
}

.section {
    padding: 40px 7vw 20px;
}

.stream-header {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 20px;
}

.stream-header h1 {
    margin: 0 0 6px;
    font-family: "Space Grotesk", Arial, sans-serif;
    font-size: 36px;
}

.stream-header p {
    margin: 0;
    color: var(--muted);
}

.stream-meta {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
}

.stream-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 18px;
    height: calc(100vh - 140px);
}

.video-panel,
.chat-panel,
.stream-cta,
.stream-landing,
.alert {
    background: var(--black-2);
    border: 1px solid #262626;
    border-radius: 18px;
    padding: 20px;
    box-shadow: 0 10px 26px rgba(0, 0, 0, 0.35);
}

.video-panel {
    position: relative;
    display: flex;
    flex-direction: column;
    min-height: 0;
}

.alert {
    color: var(--white);
    background: rgba(30, 144, 255, 0.12);
    margin-bottom: 16px;
}

.video-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 12px;
    flex: 1;
    min-height: 0;
}

.video-card {
    background: var(--black-3);
    border-radius: 14px;
    border: 1px solid #2a2a2a;
    overflow: hidden;
    position: relative;
}

.video-card video {
    width: 100%;
    height: 220px;
    object-fit: cover;
    background: #0b0f14;
}

.video-card.feature {
    grid-column: 1 / -1;
    height: 100%;
    min-height: 420px;
}

.video-card.feature video {
    height: 100%;
}

.video-label {
    position: absolute;
    left: 10px;
    bottom: 10px;
    padding: 6px 10px;
    border-radius: 999px;
    background: rgba(0, 0, 0, 0.6);
    font-size: 12px;
}

.controls {
    position: absolute;
    top: 16px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    z-index: 2;
    background: rgba(6, 10, 15, 0.7);
    padding: 8px 12px;
    border-radius: 999px;
    border: 1px solid #2a2a2a;
}

.status {
    margin-top: 12px;
    color: var(--muted);
    font-size: 13px;
}

.chat-panel h3 {
    margin: 0 0 12px;
}

.chat-panel {
    display: flex;
    flex-direction: column;
    min-height: 0;
}

.chat-messages {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    background: var(--black-3);
    border-radius: 12px;
    padding: 12px;
    border: 1px solid #2a2a2a;
    margin-bottom: 12px;
}

.chat-message {
    margin-bottom: 10px;
    line-height: 1.4;
    color: var(--white);
    font-size: 14px;
}

.chat-message span {
    color: var(--muted);
    font-size: 12px;
    margin-right: 6px;
}

.chat-input {
    display: flex;
    gap: 10px;
}

.chat-input input {
    flex: 1;
    padding: 12px;
    border-radius: 12px;
    border: 1px solid #2a2a2a;
    background: var(--black-3);
    color: var(--white);
}

.stream-landing h2 {
    margin-top: 0;
}

.stream-landing p {
    color: var(--muted);
}

.stream-cta {
    display: flex;
    gap: 12px;
    align-items: center;
    justify-content: flex-start;
}

@media (max-width: 980px) {
    .stream-grid { grid-template-columns: 1fr; height: auto; }
    .controls { position: static; transform: none; justify-content: center; margin-bottom: 12px; }
}

@media (max-width: 640px) {
    .nav { flex-direction: column; gap: 10px; }
    .nav-links { flex-wrap: wrap; justify-content: center; }
    .nav-actions { flex-wrap: wrap; justify-content: center; }
    .chat-input { flex-direction: column; }
}
</style>
</head>
<body>
<div class="page">
    <div class="ribbon"></div>
    <div class="nav">
        <div class="logo">
            <img class="logo-mark" src="/static/logo.png" alt="Aantre logo" onerror="this.style.display='none'">
            <span class="logo-text">AANTRE</span>
        </div>
        <div class="nav-links">
            <a href="/pricing">Plans</a>
            <a href="/#generate">Mashup Studio</a>
            <a href="/about">About</a>
        </div>
        <div class="nav-actions">
            <button class="btn btn-primary" type="button" onclick="createStream()">Create Stream</button>
            <button class="btn btn-outline" type="button" onclick="joinStream()">Join Stream</button>
        </div>
    </div>

    <section class="section">
        {% if room_error %}
        <div class="alert">{{ room_error }}</div>
        <div class="stream-cta">
            <button class="btn btn-primary" type="button" onclick="createStream()">Create Stream</button>
            <button class="btn btn-outline" type="button" onclick="joinStream()">Join Stream</button>
        </div>
        {% elif room_code %}
        <div class="stream-header">
            <div>
                <h1>Live Stream Room</h1>
                <p>Share this code: <strong id="room-code">{{ room_code }}</strong></p>
            </div>
            <div class="stream-meta">
                <span><strong id="viewer-count">1</strong> viewers</span>
                <button class="btn btn-ghost" type="button" onclick="copyCode()">Copy Code</button>
                <button class="btn btn-outline" type="button" onclick="leaveRoom()">Leave</button>
            </div>
        </div>
        <div class="stream-grid">
            <div class="video-panel">
                <div class="video-grid" id="video-grid">
                    <div class="video-card feature" id="local-card">
                        <video id="local-video" autoplay playsinline muted></video>
                        <div class="video-label" id="local-label">Host</div>
                    </div>
                </div>
                <div class="controls">
                    <button class="btn btn-ghost" type="button" id="enable-audio">Enable Audio</button>
                    <button class="btn btn-ghost" type="button" id="toggle-audio">Mute</button>
                    <button class="btn btn-ghost" type="button" id="toggle-video">Disable Video</button>
                    <button class="btn btn-primary" type="button" id="start-media">Start Camera</button>
                </div>
                <div class="status" id="status"></div>
            </div>
            <div class="chat-panel">
                <h3>Live Chat</h3>
                <div class="chat-messages" id="chat-messages"></div>
                <div class="chat-input">
                    <input id="chat-input" placeholder="Write a message" maxlength="500">
                    <button class="btn btn-primary" type="button" id="chat-send">Send</button>
                </div>
            </div>
        </div>
        {% else %}
        <div class="stream-landing">
            <h2>Go Live with Aantre</h2>
            <p>Create a stream to get a unique code, or join a stream using a code shared by the host.</p>
            <div class="stream-cta">
                <button class="btn btn-primary" type="button" onclick="createStream()">Create Stream</button>
                <button class="btn btn-outline" type="button" onclick="joinStream()">Join Stream</button>
            </div>
        </div>
        {% endif %}
    </section>
</div>

<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
<script>
var ROOM_CODE = "{{ room_code or '' }}";

function createStream(){
    fetch("/stream/create", { method: "POST" })
        .then(function(response){ return response.json(); })
        .then(function(data){
            if (data && data.ok && data.room_url) {
                window.location = data.room_url;
                return;
            }
            alert((data && data.error) ? data.error : "Could not create stream.");
        })
        .catch(function(){
            alert("Could not create stream.");
        });
}

function joinStream(){
    var code = prompt("Enter stream code");
    if (!code) {
        return;
    }
    code = code.trim().toUpperCase();
    if (!code) {
        return;
    }
    window.location = "/stream/" + encodeURIComponent(code);
}

function copyCode(){
    var codeEl = document.getElementById("room-code");
    if (!codeEl) {
        return;
    }
    var text = codeEl.textContent || "";
    if (!text) {
        return;
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text);
        return;
    }
    alert("Copy this code: " + text);
}

function leaveRoom(){
    window.location = "/stream";
}

if (ROOM_CODE) {
    var socket = io({ transports: ["websocket", "polling"] });
    var localStream = null;
    var peers = {};
    var displayName = "";
    var joined = false;
    var isHost = false;

    function setStatus(message) {
        var statusEl = document.getElementById("status");
        if (statusEl) {
            statusEl.textContent = message || "";
        }
    }

    function ensureName() {
        if (displayName) {
            return;
        }
        var name = prompt("Your display name");
        name = (name || "Guest").trim();
        if (!name) {
            name = "Guest";
        }
        displayName = name.substring(0, 32);
    }

    function updateViewerCount(count) {
        var countEl = document.getElementById("viewer-count");
        if (countEl && typeof count === "number") {
            countEl.textContent = String(count);
        }
    }

    function updateRoleUI() {
        var startBtn = document.getElementById("start-media");
        var audioBtn = document.getElementById("toggle-audio");
        var videoBtn = document.getElementById("toggle-video");
        var enableAudioBtn = document.getElementById("enable-audio");
        var localCard = document.getElementById("local-card");
        var localLabel = document.getElementById("local-label");

        if (isHost) {
            if (enableAudioBtn) { enableAudioBtn.style.display = "none"; }
            if (startBtn) { startBtn.style.display = "inline-flex"; }
            if (audioBtn) { audioBtn.style.display = "inline-flex"; }
            if (videoBtn) { videoBtn.style.display = "inline-flex"; }
            if (localCard) { localCard.style.display = "block"; }
            if (localLabel) { localLabel.textContent = "Host"; }
        } else {
            if (enableAudioBtn) { enableAudioBtn.style.display = "inline-flex"; }
            if (startBtn) { startBtn.style.display = "none"; }
            if (audioBtn) { audioBtn.style.display = "none"; }
            if (videoBtn) { videoBtn.style.display = "none"; }
            if (localCard) { localCard.style.display = "none"; }
        }
    }

    function enableAudienceAudio() {
        var videos = document.querySelectorAll("#video-grid video");
        videos.forEach(function(video){
            video.muted = false;
            var playPromise = video.play();
            if (playPromise && typeof playPromise.catch === "function") {
                playPromise.catch(function(){
                    // Autoplay may still be blocked.
                });
            }
        });
    }

    function attachRemote(peerId, stream) {
        var grid = document.getElementById("video-grid");
        if (!grid) {
            return;
        }
        var cardId = "peer-" + peerId;
        var existing = document.getElementById(cardId);
        if (existing) {
            var videoEl = existing.querySelector("video");
            if (videoEl) {
                videoEl.srcObject = stream;
            }
            return;
        }
        var card = document.createElement("div");
        card.className = "video-card";
        if (!isHost && !grid.querySelector(".video-card.feature")) {
            card.className += " feature";
        }
        card.id = cardId;

        var video = document.createElement("video");
        video.autoplay = true;
        video.playsInline = true;
        video.muted = !isHost;
        video.srcObject = stream;
        var playPromise = video.play();
        if (playPromise && typeof playPromise.catch === "function") {
            playPromise.catch(function(){
                // Autoplay may be blocked; user can enable audio manually.
            });
        }

        var label = document.createElement("div");
        label.className = "video-label";
        label.textContent = isHost ? "Viewer" : "Host";

        card.appendChild(video);
        card.appendChild(label);
        grid.appendChild(card);
    }

    function removePeer(peerId) {
        if (peers[peerId]) {
            peers[peerId].close();
            delete peers[peerId];
        }
        var card = document.getElementById("peer-" + peerId);
        if (card && card.parentNode) {
            card.parentNode.removeChild(card);
        }
    }

    function createPeer(peerId) {
        var pc = new RTCPeerConnection({
            iceServers: [{ urls: "stun:stun.l.google.com:19302" }]
        });
        peers[peerId] = pc;

        if (isHost) {
            if (localStream) {
                localStream.getTracks().forEach(function(track){
                    pc.addTrack(track, localStream);
                });
            } else {
                pc.addTransceiver("video", { direction: "sendonly" });
                pc.addTransceiver("audio", { direction: "sendonly" });
            }
        } else {
            pc.addTransceiver("video", { direction: "recvonly" });
            pc.addTransceiver("audio", { direction: "recvonly" });

            pc.ontrack = function(event){
                if (event.streams && event.streams[0]) {
                    attachRemote(peerId, event.streams[0]);
                }
            };
        }

        pc.onicecandidate = function(event){
            if (event.candidate) {
                socket.emit("webrtc-ice", {
                    target: peerId,
                    candidate: event.candidate
                });
            }
        };

        return pc;
    }

    function makeOffer(peerId) {
        if (!isHost) {
            return;
        }
        var pc = peers[peerId] || createPeer(peerId);
        pc.createOffer()
            .then(function(offer){
                return pc.setLocalDescription(offer);
            })
            .then(function(){
                socket.emit("webrtc-offer", {
                    target: peerId,
                    sdp: pc.localDescription
                });
            })
            .catch(function(){
                setStatus("Could not connect to a viewer.");
            });
    }

    function startLocalMedia() {
        if (!isHost) {
            return Promise.resolve(null);
        }
        if (localStream) {
            return Promise.resolve(localStream);
        }
        return navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1920 },
                height: { ideal: 1080 },
                frameRate: { ideal: 30, max: 30 }
            },
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        })
            .then(function(stream){
                localStream = stream;
                stream.getVideoTracks().forEach(function(track){
                    try {
                        track.contentHint = "detail";
                    } catch (e) {
                        // Ignore unsupported hint.
                    }
                });
                stream.getAudioTracks().forEach(function(track){
                    try {
                        track.contentHint = "music";
                    } catch (e) {
                        // Ignore unsupported hint.
                    }
                });
                var localVideo = document.getElementById("local-video");
                if (localVideo) {
                    localVideo.srcObject = stream;
                }
                Object.keys(peers).forEach(function(peerId){
                    stream.getTracks().forEach(function(track){
                        var sender = peers[peerId].addTrack(track, stream);
                        var params = sender.getParameters();
                        if (!params.encodings) {
                            params.encodings = [{}];
                        }
                        if (track.kind === "video") {
                            params.encodings[0].maxBitrate = 3500000;
                            params.degradationPreference = "maintain-framerate";
                        }
                        if (track.kind === "audio") {
                            params.encodings[0].maxBitrate = 128000;
                        }
                        sender.setParameters(params).catch(function(){
                            // Ignore bitrate cap failures.
                        });
                    });
                    makeOffer(peerId);
                });
                return stream;
            })
            .catch(function(){
                setStatus("Camera or mic blocked. You can still watch.");
                return null;
            });
    }

    function addChatMessage(data) {
        var list = document.getElementById("chat-messages");
        if (!list) {
            return;
        }
        var row = document.createElement("div");
        row.className = "chat-message";
        var time = data.time ? new Date(data.time).toLocaleTimeString() : "";
        var name = data.name || "Guest";
        var text = data.message || "";
        var stamp = document.createElement("span");
        stamp.textContent = time ? ("[" + time + "]") : "";
        row.appendChild(stamp);
        row.appendChild(document.createTextNode(" " + name + ": " + text));
        list.appendChild(row);
        list.scrollTop = list.scrollHeight;
    }

    socket.on("connect", function(){
        ensureName();
        socket.emit("join-room", { code: ROOM_CODE, name: displayName });
    });

    socket.on("room-joined", function(payload){
        joined = true;
        isHost = payload && payload.role === "host";
        updateViewerCount(payload.count || 1);
        setStatus("Connected to room " + payload.code);
        updateRoleUI();
        if (isHost) {
            startLocalMedia();
        } else {
            setStatus("You joined as a viewer. Tap Enable Audio to hear the host.");
        }
    });

    socket.on("join-error", function(payload){
        alert(payload && payload.error ? payload.error : "Could not join the room.");
        window.location = "/stream";
    });

    socket.on("peer-joined", function(payload){
        updateViewerCount(payload.count || 1);
        if (payload && payload.id) {
            makeOffer(payload.id);
        }
    });

    socket.on("peer-left", function(payload){
        updateViewerCount(payload.count || 1);
        if (payload && payload.id) {
            removePeer(payload.id);
        }
    });

    socket.on("host-ended", function(){
        alert("The host ended the stream.");
        window.location = "/stream";
    });

    socket.on("webrtc-offer", function(payload){
        var peerId = payload && payload.from;
        if (!peerId || !payload.sdp) {
            return;
        }
        var pc = peers[peerId] || createPeer(peerId);
        pc.setRemoteDescription(new RTCSessionDescription(payload.sdp))
            .then(function(){
                return pc.createAnswer();
            })
            .then(function(answer){
                return pc.setLocalDescription(answer);
            })
            .then(function(){
                socket.emit("webrtc-answer", {
                    target: peerId,
                    sdp: pc.localDescription
                });
            })
            .catch(function(){
                setStatus("Connection setup failed.");
            });
    });

    socket.on("webrtc-answer", function(payload){
        var peerId = payload && payload.from;
        if (!peerId || !payload.sdp || !peers[peerId]) {
            return;
        }
        peers[peerId].setRemoteDescription(new RTCSessionDescription(payload.sdp));
    });

    socket.on("webrtc-ice", function(payload){
        var peerId = payload && payload.from;
        if (!peerId || !payload.candidate || !peers[peerId]) {
            return;
        }
        peers[peerId].addIceCandidate(new RTCIceCandidate(payload.candidate));
    });

    socket.on("chat-message", function(payload){
        addChatMessage(payload || {});
    });

    var startBtn = document.getElementById("start-media");
    if (startBtn) {
        startBtn.addEventListener("click", function(){
            startLocalMedia();
        });
    }

    var enableAudioBtn = document.getElementById("enable-audio");
    if (enableAudioBtn) {
        enableAudioBtn.addEventListener("click", function(){
            enableAudienceAudio();
        });
    }

    var audioBtn = document.getElementById("toggle-audio");
    if (audioBtn) {
        audioBtn.addEventListener("click", function(){
            if (!isHost) {
                return;
            }
            if (!localStream) {
                setStatus("Start camera first.");
                return;
            }
            localStream.getAudioTracks().forEach(function(track){
                track.enabled = !track.enabled;
                audioBtn.textContent = track.enabled ? "Mute" : "Unmute";
            });
        });
    }

    var videoBtn = document.getElementById("toggle-video");
    if (videoBtn) {
        videoBtn.addEventListener("click", function(){
            if (!isHost) {
                return;
            }
            if (!localStream) {
                setStatus("Start camera first.");
                return;
            }
            localStream.getVideoTracks().forEach(function(track){
                track.enabled = !track.enabled;
                videoBtn.textContent = track.enabled ? "Disable Video" : "Enable Video";
            });
        });
    }

    var chatSend = document.getElementById("chat-send");
    var chatInput = document.getElementById("chat-input");
    function sendChat(){
        if (!chatInput) {
            return;
        }
        var text = chatInput.value.trim();
        if (!text) {
            return;
        }
        chatInput.value = "";
        socket.emit("chat-message", { message: text });
    }

    if (chatSend) {
        chatSend.addEventListener("click", sendChat);
    }

    if (chatInput) {
        chatInput.addEventListener("keydown", function(event){
            if (event.key === "Enter") {
                sendChat();
            }
        });
    }

    window.addEventListener("beforeunload", function(){
        socket.emit("leave-room");
    });
}
</script>
</body>
</html>
"""

def cleanup_after_email(session_id=None):
    """Clean up generated files and delete songs from MongoDB after email sent."""
    def delayed_cleanup():
        sleep(15)
        
        if mongo_handler.connected and session_id:
            mongo_handler.delete_session_songs(session_id)
        
        for f in ("result.mp3", "result.zip"):
            try:
                if os.path.exists(f):
                    os.remove(f)
                    print(f"✅ Deleted: {f}")
            except Exception as e:
                print(f"⚠️ Could not delete {f}: {e}")
        
        try:
            if os.path.exists(DOWNLOAD_DIR):
                for file in os.listdir(DOWNLOAD_DIR):
                    try:
                        os.remove(os.path.join(DOWNLOAD_DIR, file))
                    except:
                        pass
                print(f"✅ Cleared {DOWNLOAD_DIR}")
        except Exception as e:
            print(f"⚠️ Could not clear downloads: {e}")

        try:
            if os.path.exists(TRIM_DIR):
                for file in os.listdir(TRIM_DIR):
                    try:
                        os.remove(os.path.join(TRIM_DIR, file))
                    except:
                        pass
                print(f"✅ Cleared {TRIM_DIR}")
        except Exception as e:
            print(f"⚠️ Could not clear trimmed: {e}")
    
    threading.Thread(target=delayed_cleanup, daemon=True).start()

def send_email(to_email, zip_path):
    """Send email via subprocess with optimized error handling"""
    load_dotenv(override=True)

    if not os.path.exists(zip_path):
        print(f"⚠ Zip file not found: {zip_path}")
        return False

    try:
        result = subprocess.run(
            [sys.executable, "send_email_job.py", to_email, zip_path],
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout.strip())
        return result.returncode == 0
    except Exception as e:
        print(f"Email job failed: {e}")
        return False

@app.route("/get-artist-info", methods=["GET"])
def get_artist_info():
    """Optimized artist info retrieval"""
    from mashup_core import ARTIST_INFO

    result = {"thumbnail": ARTIST_INFO.get("thumbnail", ""), "first_audio": ""}
    
    if os.path.exists(DOWNLOAD_DIR):
        files = os.listdir(DOWNLOAD_DIR)
        if files:
            result["first_audio"] = f"/audio/{files[0]}"
    
    return result


@app.route("/stream", methods=["GET"])
def stream_home():
    return render_template_string(STREAM_HTML, room_code=None, room_error=None)


@app.route("/stream/create", methods=["POST"])
def stream_create():
    try:
        code = create_stream_room()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": True, "code": code, "room_url": f"/stream/{code}"})


@app.route("/stream/<code>", methods=["GET"])
def stream_room(code):
    normalized = normalize_stream_code(code)
    room = get_stream_room(normalized)
    if not room:
        return render_template_string(
            STREAM_HTML,
            room_code=None,
            room_error="Stream not found or ended.",
        ), 404
    return render_template_string(STREAM_HTML, room_code=normalized, room_error=None)

@app.route("/audio/<filename>", methods=["GET"])
def serve_audio(filename):
    """Serve audio files from downloads directory"""
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    return send_file(filepath, mimetype="audio/mpeg") if os.path.exists(filepath) else ("File not found", 404)


def _remove_participant(sid, notify=True):
    LAST_CHAT_BY_SID.pop(sid, None)
    code = SOCKET_ROOM_BY_SID.pop(sid, None)
    if not code:
        return

    participants = STREAM_PARTICIPANTS.get(code)
    if participants and sid in participants:
        name = participants.pop(sid)
        if notify:
            emit("peer-left", {"id": sid, "name": name, "count": len(participants)}, room=code)

    if STREAM_HOSTS.get(code) == sid:
        STREAM_HOSTS.pop(code, None)
        if participants:
            for participant_id in list(participants.keys()):
                SOCKET_ROOM_BY_SID.pop(participant_id, None)
        if notify:
            emit("host-ended", {}, room=code)
        STREAM_PARTICIPANTS.pop(code, None)
        update_stream_status(code, False)
        return

    if not participants:
        STREAM_PARTICIPANTS.pop(code, None)
        update_stream_status(code, False)
    else:
        touch_stream_room(code)


@socketio.on("join-room")
def handle_join_room(data):
    code = normalize_stream_code((data or {}).get("code", ""))
    name = ((data or {}).get("name") or "Guest").strip()[:32]

    room = get_stream_room(code)
    if not room:
        emit("join-error", {"error": "Room not found or ended."})
        return

    participants = STREAM_PARTICIPANTS.setdefault(code, {})
    if len(participants) >= STREAM_ROOM_MAX:
        emit("join-error", {"error": "Room is full."})
        return

    host_id = STREAM_HOSTS.get(code)
    if host_id and host_id not in participants:
        STREAM_HOSTS.pop(code, None)
        host_id = None
    if not host_id:
        STREAM_HOSTS[code] = request.sid
        host_id = request.sid

    join_room(code)
    participants[request.sid] = name
    SOCKET_ROOM_BY_SID[request.sid] = code

    peers = [
        {"id": sid, "name": pname}
        for sid, pname in participants.items()
        if sid != request.sid
    ]

    emit(
        "room-joined",
        {
            "code": code,
            "name": name,
            "peers": peers,
            "max_size": STREAM_ROOM_MAX,
            "count": len(participants),
            "role": "host" if request.sid == host_id else "viewer",
        },
    )

    emit(
        "peer-joined",
        {"id": request.sid, "name": name, "count": len(participants)},
        room=code,
        include_self=False,
    )
    touch_stream_room(code)


@socketio.on("leave-room")
def handle_leave_room():
    code = SOCKET_ROOM_BY_SID.get(request.sid)
    if code:
        leave_room(code)
    _remove_participant(request.sid)


@socketio.on("disconnect")
def handle_disconnect():
    _remove_participant(request.sid)


@socketio.on("chat-message")
def handle_chat_message(data):
    code = SOCKET_ROOM_BY_SID.get(request.sid)
    if not code:
        return
    message = ((data or {}).get("message") or "").strip()
    if not message:
        return
    message = message[:500]
    now = datetime.utcnow().timestamp()
    last_time = LAST_CHAT_BY_SID.get(request.sid, 0)
    if now - last_time < 0.6:
        return
    LAST_CHAT_BY_SID[request.sid] = now
    name = STREAM_PARTICIPANTS.get(code, {}).get(request.sid, "Guest")
    emit(
        "chat-message",
        {
            "name": name,
            "message": message,
            "time": datetime.utcnow().isoformat() + "Z",
        },
        room=code,
    )


@socketio.on("webrtc-offer")
def handle_webrtc_offer(data):
    target = (data or {}).get("target")
    sdp = (data or {}).get("sdp")
    if not target or not sdp:
        return
    if SOCKET_ROOM_BY_SID.get(target) != SOCKET_ROOM_BY_SID.get(request.sid):
        return
    emit("webrtc-offer", {"from": request.sid, "sdp": sdp}, to=target)


@socketio.on("webrtc-answer")
def handle_webrtc_answer(data):
    target = (data or {}).get("target")
    sdp = (data or {}).get("sdp")
    if not target or not sdp:
        return
    if SOCKET_ROOM_BY_SID.get(target) != SOCKET_ROOM_BY_SID.get(request.sid):
        return
    emit("webrtc-answer", {"from": request.sid, "sdp": sdp}, to=target)


@socketio.on("webrtc-ice")
def handle_webrtc_ice(data):
    target = (data or {}).get("target")
    candidate = (data or {}).get("candidate")
    if not target or not candidate:
        return
    if SOCKET_ROOM_BY_SID.get(target) != SOCKET_ROOM_BY_SID.get(request.sid):
        return
    emit("webrtc-ice", {"from": request.sid, "candidate": candidate}, to=target)

@app.route("/", methods=["GET","POST"])
def home():
    msg_single = None
    ok_single = False
    msg_multi = None
    ok_multi = False

    if request.method == "POST":
        form_type = request.form.get("form_type", "single")

        if form_type == "multi":
            try:
                mode = request.form.get("multi_mode", "singer").strip().lower()
                queries = [q.strip() for q in request.form.getlist("queries") if q.strip()]

                total_videos = None
                if mode == "singer":
                    total_videos = int(request.form["n_multi"])
                dur = int(request.form["dur_multi"])
                email = request.form["email_multi"].strip()

                if dur <= 20:
                    raise RuntimeError("Duration must be greater than 20 seconds")

                session_id = run_multi_mashup(queries, total_videos, dur, "result.mp3", email, mode=mode)

                with zipfile.ZipFile("result.zip", "w") as z:
                    z.write("result.mp3")

                email_sent = send_email(email, "result.zip")

                if email_sent:
                    msg_multi = "✅ Premium multi mashup generated and emailed successfully!"
                    ok_multi = True
                    cleanup_after_email(session_id)
                else:
                    msg_multi = "⚠️ Multi mashup created but email failed. File is ready at: result.zip"

            except Exception as e:
                msg_multi = str(e)

        else:
            try:
                singer = request.form["singer"]
                n = int(request.form["n"])
                dur = int(request.form["dur"])
                email = request.form["email"]

                if n <= 10 or dur <= 20:
                    raise RuntimeError("Videos must be >10 and duration >20")

                session_id = run_mashup(singer, n, dur, "result.mp3", email)

                with zipfile.ZipFile("result.zip", "w") as z:
                    z.write("result.mp3")

                email_sent = send_email(email, "result.zip")

                if email_sent:
                    msg_single = "✅ Mashup generated and emailed successfully!"
                    ok_single = True
                    cleanup_after_email(session_id)
                else:
                    msg_single = "⚠️ Mashup created but email failed. File is ready at: result.zip"

            except Exception as e:
                msg_single = str(e)

    return render_template_string(
        HOME_HTML,
        msg_single=msg_single,
        ok_single=ok_single,
        msg_multi=msg_multi,
        ok_multi=ok_multi,
        ok_any=bool(ok_single or ok_multi),
    )

@app.route("/pricing", methods=["GET"])
def pricing():
    return render_template_string(PRICING_HTML)

@app.route("/about", methods=["GET"])
def about():
    return render_template_string(ABOUT_HTML)

@app.route("/generate", methods=["GET"])
def generate():
    return redirect("/#generate")


if __name__ == "__main__":
    socketio.run(app, debug=False, use_reloader=False)