# src/routes/ai.py
from flask import Blueprint, request, jsonify, current_app
from openai import OpenAI
from dotenv import load_dotenv
import os
import os, time, sqlite3, uuid, json
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, send_from_directory, render_template, session
from dotenv import load_dotenv
from flask_cors import CORS
from openai import OpenAI


# -- load env once
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_KEY:
    # সার্ভার স্টার্টেই ধরা পড়বে
    raise RuntimeError("OPENAI_API_KEY is missing in .env")

# -- init openai client once
client = OpenAI(api_key=OPENAI_KEY)

ai_bp = Blueprint("ai", __name__)

# -- Company/system context (উত্তরগুলো consistent হবে)
SYSTEM_PROMPT = (
    "You are the AI assistant for DMS MEHEDI. "
    "Answer in clear, concise English. "
    "Company focus: Digital Marketing (SEO/SEM, Google Ads & FB Ads, content, analytics), "
    "Front-end and Backend web development, Shopify dropshipping. "
    "Experience: 4+ years; Roles: Head of Marketing at Move X Health; worked with Hello Matlab Grocery and Softollyo. "
    "When asked about pricing, briefly outline tiers and invite to contact for bespoke quotes. "
    "Do not invent private data; keep paragraphs short; use bullet points when helpful."
    "Answer in clear, concise English"
    "💡 Frequent user queries to handle:\n"
    "- What’s included in your SEO Starter vs Pro plan?\n"
    "- Which technologies do you use for web & app development?\n"
    "- How do you report results and KPIs to clients?\n"
    "- Can you help with AI search inclusion (ChatGPT, Gemini, Perplexity)?\n"
    "- Do you provide Shopify SEO and conversion optimization?\n"
    "- How do you track SEO performance? (traffic, keywords, CTR, conversions)\n"
    "- Do you prepare websites for AI search visibility?\n"
    "- What’s included in Technical SEO? (site speed, schema, sitemaps)\n"
    "- How do you handle Local SEO for multiple markets?\n"
    "- Do you create SEO content and landing pages?\n"
    "- Can you optimize Google Ads with GA4 reporting?\n"
    "- Do you offer Facebook Ads campaign management?\n"
    "- How do you structure backlink building strategies?\n"
    "- What is your content strategy for ranking blogs?\n"
    "- Do you set up Google Business Profile for local SEO?\n"
    "- How do you improve Core Web Vitals and page speed?\n"
    "- Do you help with eCommerce (Shopify, WooCommerce, WordPress) SEO?\n"
    "- Can you create conversion-focused landing pages?\n"
    "- Do you provide competitor SEO analysis and keyword research?\n"
    "- How do you handle multi-language or international SEO?\n"
    "- Do you help with YouTube SEO and video ranking?\n"
    "- Can you integrate AI tools into websites for better engagement?\n"
    "How do you rank a new website fast on Google?"
    "What are the best tools for keyword research in 2025?"
    "How can you optimize content for Google’s Helpful Content Update?"
    "What’s the difference between on-page SEO and off-page SEO?"
    "How do you use AI (ChatGPT, Gemini, Claude) for SEO content writing?"
    "How do you track and improve Domain Authority (DA/DR)?"
    "What are the top backlink strategies that actually work in 2025?"
    "How do you structure pillar pages and topic clusters for SEO?"
    "Can you integrate Google Analytics 4 (GA4) with Google Ads for better ROI?"
    "How do you run Performance Max campaigns effectively?"
    "What are the top strategies for ranking local businesses on Google Maps?"
    "How do you optimize voice search (Siri, Alexa, Google Assistant) for SEO?"
    "What’s the role of E-E-A-T in Google ranking and how do you improve it?"
    "How do you optimize an eCommerce store for both SEO and conversions?"
    "How do you prepare content for AI Overviews in Google Search?"
)


def ask_openai(question: str) -> str:
    """Call OpenAI and return a plain text answer."""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",        # চাইলে অন্য মডেল ব্যবহার করতে পারো
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ],
        temperature=0.5,
    )
    return resp.choices[0].message.content

@ai_bp.route("/ai", methods=["POST"])
def ai():
    """POST /api/ai  ->  {question: "..."}"""
    try:
        data = request.get_json(force=True) or {}
        question = (data.get("question") or "").strip()
        if not question:
            return jsonify({"ok": False, "error": "Empty question"}), 400

        text = ask_openai(question)
        return jsonify({"ok": True, "text": text}), 200

    except Exception as e:
        current_app.logger.exception("AI route failed")
        return jsonify({"ok": False, "error": str(e)}), 500