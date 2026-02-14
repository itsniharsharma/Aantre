from flask import Flask, request, render_template_string, send_file, redirect
import zipfile
import os
import subprocess
import sys
import threading
from time import sleep
from dotenv import load_dotenv
from mashup_core import run_mashup, DOWNLOAD_DIR, TRIM_DIR
from mongodb_helper import mongo_handler

V2_DIR = os.path.join(os.path.dirname(__file__), "v-2-multimash")
if V2_DIR not in sys.path:
    sys.path.insert(0, V2_DIR)

from multimash_core import run_multi_mashup

load_dotenv()
app = Flask(__name__)

HOME_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Aantre — AI Mashup Generator</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Space+Grotesk:wght@500;600&display=swap" rel="stylesheet">

<style>
:root {
    --black: #0b0b0b;
    --black-2: #121212;
    --black-3: #1a1a1a;
    --violet: #9b5cff;
    --violet-2: #7a3cf0;
    --violet-3: #c4a7ff;
    --white: #ffffff;
    --muted: #b7b7b7;
}

* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: "DM Sans", Arial, sans-serif;
    color: var(--white);
    background: radial-gradient(1200px 600px at 20% -10%, #2a1f4a 0%, transparent 60%),
                radial-gradient(900px 500px at 90% 0%, #1c1239 0%, transparent 60%),
                var(--black);
    -webkit-text-size-adjust: 100%;
}

a { color: inherit; text-decoration: none; }

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
    background: radial-gradient(circle at 30% 30%, var(--violet), var(--violet-2));
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
    font-family: "Space Grotesk", Arial, sans-serif;
    font-size: 26px;
    letter-spacing: 1px;
    color: var(--white);
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

.headline {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    margin-bottom: 18px;
}

.headline h1 {
    font-family: "Space Grotesk", Arial, sans-serif;
    font-size: 54px;
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
    background: rgba(155, 92, 255, 0.16);
    color: var(--violet-3);
    font-weight: 600;
    white-space: nowrap;
}

.btn {
    border: none;
    padding: 14px 20px;
    border-radius: 999px;
    font-weight: 600;
    cursor: pointer;
    transition: 0.2s;
}

.btn-primary {
    background: var(--violet);
    color: var(--black);
}

.btn-outline {
    background: transparent;
    color: var(--white);
    border: 2px solid var(--white);
}

.btn:hover { transform: translateY(-2px); }

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
    background: var(--violet);
    color: var(--black);
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
    background: var(--violet);
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
    border-top-color: var(--violet);
    border-right-color: var(--violet-3);
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
    background: rgba(155, 92, 255, 0.08);
    color: var(--violet-3);
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
    try {
        localStorage.setItem("mashup_in_progress", "1");
    } catch (e) {
        // localStorage may be blocked; continue without persistence.
    }
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

    var ok = document.body.getAttribute("data-ok");
    if (ok === "1") {
        try {
            localStorage.removeItem("mashup_in_progress");
        } catch (e) {
            // Ignore storage errors.
        }
        loader.style.display = "none";
        return;
    }

    var inProgress = false;
    try {
        inProgress = localStorage.getItem("mashup_in_progress") === "1";
    } catch (e) {
        inProgress = false;
    }

    if (inProgress) {
        loader.style.display = "flex";
    }
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
</script>

</head>

<body data-ok="{{ 1 if ok_any else 0 }}">
<div class="page">
    <div class="ribbon"></div>

    <div class="nav">
        <div class="logo">AANTRE</div>
        <div class="nav-links">
            <a href="/pricing">Pricing</a>
            <a href="/#generate">Generate</a>
            <a href="/about">About</a>
        </div>
    </div>

    <section class="section" id="showcase">
        <div class="headline">
            <div>
                <h1>Craft your favorite singer mashup in minutes.</h1>
                <p>Aantre is a version-1, software-in-a-box experience for Bollywood mashups with clean trims, automated search, and instant delivery.</p>
            </div>
            <div class="badge">Version 1 - Software in a Box</div>
        </div>
        <h2>Bollywood Voices Carousel</h2>
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
        <h2>Generate Your Mashup</h2>
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

                <button class="btn btn-primary" type="submit">Generate Mashup and Email</button>

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
        <h2>Generate Multi Mashup (V2)</h2>
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

                <button class="btn btn-primary" type="submit">Generate Premium Multi Mashup</button>
            </form>
        </div>
    </section>

    <section class="section" id="features">
        <h2>Core Features</h2>
        <div class="cards">
            <div class="card">
                <h3>Smart Search</h3>
                <p>Fetches top tracks by artist for high-quality mashups.</p>
            </div>
            <div class="card">
                <h3>Clean Stitch</h3>
                <p>Seamless merges that preserve clarity and punch.</p>
            </div>
            <div class="card">
                <h3>Instant Delivery</h3>
                <p>Zip and email workflow from a single click.</p>
            </div>
        </div>
    </section>

    <section class="section" id="coming-soon">
        <h2>Coming Soon</h2>
        <div class="coming-soon">Thapar creators will be able to sing, post, and showcase their own mashups inside Aantre.</div>
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
<title>Aantre — Pricing</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Space+Grotesk:wght@500;600&display=swap" rel="stylesheet">

<style>
:root {
    --black: #0b0b0b;
    --black-2: #121212;
    --black-3: #1a1a1a;
    --violet: #9b5cff;
    --violet-2: #7a3cf0;
    --violet-3: #c4a7ff;
    --white: #ffffff;
    --muted: #b7b7b7;
}

* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: "DM Sans", Arial, sans-serif;
    color: var(--white);
    background: radial-gradient(1200px 600px at 20% -10%, #2a1f4a 0%, transparent 60%),
                radial-gradient(900px 500px at 90% 0%, #1c1239 0%, transparent 60%),
                var(--black);
}

a { color: inherit; text-decoration: none; }

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
    background: radial-gradient(circle at 30% 30%, var(--violet), var(--violet-2));
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
    font-family: "Space Grotesk", Arial, sans-serif;
    font-size: 26px;
    letter-spacing: 1px;
    color: var(--white);
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
    color: var(--violet);
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
    .section h1 { font-size: 40px; }
}
</style>
</head>
<body>
<div class="page">
    <div class="ribbon"></div>
    <div class="nav">
        <div class="logo">AANTRE</div>
        <div class="nav-links">
            <a href="/pricing">Pricing</a>
            <a href="/#generate">Generate</a>
            <a href="/about">About</a>
        </div>
    </div>

    <section class="section">
        <h1>Pricing</h1>
        <p>Simple, early-access pricing while we build the full creator community.</p>
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
    </section>

    <footer class="footer">
        <div class="footer-bottom">
            <span>© 2026 Aantre. All rights reserved.</span>
            <span>Version 1 pricing.</span>
        </div>
    </footer>
</div>
</body>
</html>
"""

ABOUT_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Aantre — About</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Space+Grotesk:wght@500;600&display=swap" rel="stylesheet">

<style>
:root {
    --black: #0b0b0b;
    --black-2: #121212;
    --black-3: #1a1a1a;
    --violet: #9b5cff;
    --violet-2: #7a3cf0;
    --violet-3: #c4a7ff;
    --white: #ffffff;
    --muted: #b7b7b7;
}

* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: "DM Sans", Arial, sans-serif;
    color: var(--white);
    background: radial-gradient(1200px 600px at 20% -10%, #2a1f4a 0%, transparent 60%),
                radial-gradient(900px 500px at 90% 0%, #1c1239 0%, transparent 60%),
                var(--black);
}

a { color: inherit; text-decoration: none; }

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
    background: radial-gradient(circle at 30% 30%, var(--violet), var(--violet-2));
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
    font-family: "Space Grotesk", Arial, sans-serif;
    font-size: 26px;
    letter-spacing: 1px;
    color: var(--white);
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
    .section h1 { font-size: 40px; }
}
</style>
</head>
<body>
<div class="page">
    <div class="ribbon"></div>
    <div class="nav">
        <div class="logo">AANTRE</div>
        <div class="nav-links">
            <a href="/pricing">Pricing</a>
            <a href="/#generate">Generate</a>
            <a href="/about">About</a>
        </div>
    </div>

    <section class="section">
        <h1>About</h1>
        <div class="info-card">
            <p>Hi, I am Nihar Sharma. I am building Aantre as a version-1, software-in-a-box experience that helps people generate Bollywood mashups quickly and cleanly.</p>
            <p>If you are interested in building your passion, let us team up and create something meaningful together.</p>
            <p>Connect on LinkedIn: <a href="https://www.linkedin.com/in/itsniharsharma/" target="_blank" rel="noopener">https://www.linkedin.com/in/itsniharsharma/</a></p>
            <h3>Version 1 Features</h3>
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

@app.route("/audio/<filename>", methods=["GET"])
def serve_audio(filename):
    """Serve audio files from downloads directory"""
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    return send_file(filepath, mimetype="audio/mpeg") if os.path.exists(filepath) else ("File not found", 404)

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
    app.run(debug=False, use_reloader=False)