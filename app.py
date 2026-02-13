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

load_dotenv()
app = Flask(__name__)

# -----------------------
# PROFESSIONAL FRONTEND
# -----------------------

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
    min-width: 240px;
    padding: 14px 16px;
    border-radius: 16px;
    border: 1px solid #2c2c2c;
    background: var(--black-3);
}

.singer-card img {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid var(--violet);
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
    .singer-card img { width: 54px; height: 54px; }
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
function showLoader(){
    document.getElementById("loader").style.display = "flex";
}
</script>

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
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Arijit%20Singh" alt="Arijit Singh">
                    <div>
                        <h3>Arijit Singh</h3>
                        <span>Romantic ballads</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Shreya%20Ghoshal" alt="Shreya Ghoshal">
                    <div>
                        <h3>Shreya Ghoshal</h3>
                        <span>Classical fusion</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Sonu%20Nigam" alt="Sonu Nigam">
                    <div>
                        <h3>Sonu Nigam</h3>
                        <span>Evergreen hits</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Sunidhi%20Chauhan" alt="Sunidhi Chauhan">
                    <div>
                        <h3>Sunidhi Chauhan</h3>
                        <span>Power vocals</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Atif%20Aslam" alt="Atif Aslam">
                    <div>
                        <h3>Atif Aslam</h3>
                        <span>Signature timbre</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Neha%20Kakkar" alt="Neha Kakkar">
                    <div>
                        <h3>Neha Kakkar</h3>
                        <span>Dance anthems</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Armaan%20Malik" alt="Armaan Malik">
                    <div>
                        <h3>Armaan Malik</h3>
                        <span>Soft pop tone</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Kishore%20Kumar" alt="Kishore Kumar">
                    <div>
                        <h3>Kishore Kumar</h3>
                        <span>Legendary classics</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Lata%20Mangeshkar" alt="Lata Mangeshkar">
                    <div>
                        <h3>Lata Mangeshkar</h3>
                        <span>Golden era icon</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Asha%20Bhosle" alt="Asha Bhosle">
                    <div>
                        <h3>Asha Bhosle</h3>
                        <span>Timeless versatility</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Mohammed%20Rafi" alt="Mohammed Rafi">
                    <div>
                        <h3>Mohammed Rafi</h3>
                        <span>Classic melodies</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Mukesh" alt="Mukesh">
                    <div>
                        <h3>Mukesh</h3>
                        <span>Golden voice</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Udit%20Narayan" alt="Udit Narayan">
                    <div>
                        <h3>Udit Narayan</h3>
                        <span>90s romance</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Kumar%20Sanu" alt="Kumar Sanu">
                    <div>
                        <h3>Kumar Sanu</h3>
                        <span>90s chart hits</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Alka%20Yagnik" alt="Alka Yagnik">
                    <div>
                        <h3>Alka Yagnik</h3>
                        <span>Melodic charm</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=S.%20P.%20Balasubrahmanyam" alt="S. P. Balasubrahmanyam">
                    <div>
                        <h3>S. P. Balasubrahmanyam</h3>
                        <span>Pan-India legend</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Shaan" alt="Shaan">
                    <div>
                        <h3>Shaan</h3>
                        <span>Feel-good pop</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=KK" alt="KK">
                    <div>
                        <h3>KK</h3>
                        <span>Soulful hits</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Mohit%20Chauhan" alt="Mohit Chauhan">
                    <div>
                        <h3>Mohit Chauhan</h3>
                        <span>Indie romance</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Jubin%20Nautiyal" alt="Jubin Nautiyal">
                    <div>
                        <h3>Jubin Nautiyal</h3>
                        <span>Modern ballads</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Badshah" alt="Badshah">
                    <div>
                        <h3>Badshah</h3>
                        <span>Hip-hop hooks</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Honey%20Singh" alt="Honey Singh">
                    <div>
                        <h3>Honey Singh</h3>
                        <span>Party anthems</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Diljit%20Dosanjh" alt="Diljit Dosanjh">
                    <div>
                        <h3>Diljit Dosanjh</h3>
                        <span>Punjabi crossover</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Mika%20Singh" alt="Mika Singh">
                    <div>
                        <h3>Mika Singh</h3>
                        <span>High energy hits</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Vishal%20Dadlani" alt="Vishal Dadlani">
                    <div>
                        <h3>Vishal Dadlani</h3>
                        <span>Rock edge</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Shekhar%20Ravjiani" alt="Shekhar Ravjiani">
                    <div>
                        <h3>Shekhar Ravjiani</h3>
                        <span>Smooth hooks</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Shankar%20Mahadevan" alt="Shankar Mahadevan">
                    <div>
                        <h3>Shankar Mahadevan</h3>
                        <span>Carnatic power</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Hariharan" alt="Hariharan">
                    <div>
                        <h3>Hariharan</h3>
                        <span>Ghazi gharana</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Sukhwinder%20Singh" alt="Sukhwinder Singh">
                    <div>
                        <h3>Sukhwinder Singh</h3>
                        <span>Stage fire</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Javed%20Ali" alt="Javed Ali">
                    <div>
                        <h3>Javed Ali</h3>
                        <span>Romantic tone</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Kailash%20Kher" alt="Kailash Kher">
                    <div>
                        <h3>Kailash Kher</h3>
                        <span>Sufi soul</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Rahat%20Fateh%20Ali%20Khan" alt="Rahat Fateh Ali Khan">
                    <div>
                        <h3>Rahat Fateh Ali Khan</h3>
                        <span>Qawwali depth</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Nusrat%20Fateh%20Ali%20Khan" alt="Nusrat Fateh Ali Khan">
                    <div>
                        <h3>Nusrat Fateh Ali Khan</h3>
                        <span>Qawwali master</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Benny%20Dayal" alt="Benny Dayal">
                    <div>
                        <h3>Benny Dayal</h3>
                        <span>Groove pop</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Neeti%20Mohan" alt="Neeti Mohan">
                    <div>
                        <h3>Neeti Mohan</h3>
                        <span>Modern shine</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Shilpa%20Rao" alt="Shilpa Rao">
                    <div>
                        <h3>Shilpa Rao</h3>
                        <span>Sultry tone</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Monali%20Thakur" alt="Monali Thakur">
                    <div>
                        <h3>Monali Thakur</h3>
                        <span>Soft pop</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Palak%20Muchhal" alt="Palak Muchhal">
                    <div>
                        <h3>Palak Muchhal</h3>
                        <span>Love songs</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Tulsi%20Kumar" alt="Tulsi Kumar">
                    <div>
                        <h3>Tulsi Kumar</h3>
                        <span>Pop romance</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Kanika%20Kapoor" alt="Kanika Kapoor">
                    <div>
                        <h3>Kanika Kapoor</h3>
                        <span>Dance sparkle</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Dhvani%20Bhanushali" alt="Dhvani Bhanushali">
                    <div>
                        <h3>Dhvani Bhanushali</h3>
                        <span>Youth pop</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Jonita%20Gandhi" alt="Jonita Gandhi">
                    <div>
                        <h3>Jonita Gandhi</h3>
                        <span>Fresh vocals</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Asees%20Kaur" alt="Asees Kaur">
                    <div>
                        <h3>Asees Kaur</h3>
                        <span>Warm tone</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=B%20Praak" alt="B Praak">
                    <div>
                        <h3>B Praak</h3>
                        <span>Emotive power</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Arko" alt="Arko">
                    <div>
                        <h3>Arko</h3>
                        <span>Indie mood</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Ankit%20Tiwari" alt="Ankit Tiwari">
                    <div>
                        <h3>Ankit Tiwari</h3>
                        <span>Dark romance</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Darshan%20Raval" alt="Darshan Raval">
                    <div>
                        <h3>Darshan Raval</h3>
                        <span>Pop ballads</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Gajendra%20Verma" alt="Gajendra Verma">
                    <div>
                        <h3>Gajendra Verma</h3>
                        <span>Indie love</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Lucky%20Ali" alt="Lucky Ali">
                    <div>
                        <h3>Lucky Ali</h3>
                        <span>Acoustic soul</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Adnan%20Sami" alt="Adnan Sami">
                    <div>
                        <h3>Adnan Sami</h3>
                        <span>Piano melodies</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Abhijeet%20Bhattacharya" alt="Abhijeet Bhattacharya">
                    <div>
                        <h3>Abhijeet Bhattacharya</h3>
                        <span>Bollywood hits</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Kavita%20Krishnamurthy" alt="Kavita Krishnamurthy">
                    <div>
                        <h3>Kavita Krishnamurthy</h3>
                        <span>Classic elegance</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Sadhana%20Sargam" alt="Sadhana Sargam">
                    <div>
                        <h3>Sadhana Sargam</h3>
                        <span>Smooth melodies</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Mahalakshmi%20Iyer" alt="Mahalakshmi Iyer">
                    <div>
                        <h3>Mahalakshmi Iyer</h3>
                        <span>Silky vocals</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Roop%20Kumar%20Rathod" alt="Roop Kumar Rathod">
                    <div>
                        <h3>Roop Kumar Rathod</h3>
                        <span>Ghazal touch</span>
                    </div>
                </div>
                <div class="singer-card">
                    <img src="https://api.dicebear.com/7.x/avataaars/png?seed=Nooran%20Sisters" alt="Nooran Sisters">
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
            {% if msg %}
            <div class="{{'success' if ok else 'error'}}">{{msg}}</div>
            {% endif %}

            <form method="post" onsubmit="showLoader()">
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
                        <h3>Your mashup is generating</h3>
                        <p>Kindly have patience and check your mail.</p>
                    </div>
                </div>
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

# -----------------------
# CLEANUP & DATABASE
# -----------------------

def cleanup_after_email(session_id=None):
    """Clean up generated files and delete songs from MongoDB after email sent."""
    def delayed_cleanup():
        sleep(15)  # Wait 15 seconds after email
        
        # Delete songs from MongoDB first
        if mongo_handler.connected and session_id:
            mongo_handler.delete_session_songs(session_id)
        
        # Delete result files
        for f in ("result.mp3", "result.zip"):
            try:
                if os.path.exists(f):
                    os.remove(f)
                    print(f"✅ Deleted: {f}")
            except Exception as e:
                print(f"⚠️ Could not delete {f}: {e}")
        
        # Clear downloads and trimmed folders efficiently
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
    
    # Run cleanup in background thread
    threading.Thread(target=delayed_cleanup, daemon=True).start()

# -----------------------
# EMAIL
# -----------------------

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


# -----------------------
# ROUTE
# -----------------------

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
    if request.method == "POST":
        try:
            singer = request.form["singer"]
            n = int(request.form["n"])
            dur = int(request.form["dur"])
            email = request.form["email"]

            if n <= 10 or dur <= 20:
                return render_template_string(HOME_HTML,
                    msg="Videos must be >10 and duration >20",
                    ok=False)

            session_id = run_mashup(singer, n, dur, "result.mp3", email)

            with zipfile.ZipFile("result.zip", "w") as z:
                z.write("result.mp3")

            email_sent = send_email(email, "result.zip")

            if email_sent:
                msg_text = "✅ Mashup generated and emailed successfully!"
                # Start cleanup in background after email
                cleanup_after_email(session_id)
            else:
                msg_text = "⚠️ Mashup created but email failed. File is ready at: result.zip"

            return render_template_string(HOME_HTML, msg=msg_text, ok=email_sent)

        except Exception as e:
            return render_template_string(HOME_HTML,
                msg=str(e),
                ok=False)

    return render_template_string(HOME_HTML, msg=None)

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