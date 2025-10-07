from flask import Blueprint, request, jsonify, render_template_string
import json
import os

cms_bp = Blueprint('cms', __name__)

# Content storage file
CONTENT_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'content.json')

# Default content structure
DEFAULT_CONTENT = {
    "hero": {
        "title": "Hi, I'm DMS MEHEDI",
        "subtitle_roles": [
            "Digital Marketing Expert",
            "Web Developer", 
            "Shopify Dropshipping Specialist"
        ],
        "description": "I help businesses grow through strategic digital marketing, modern web development, and profitable Shopify dropshipping solutions. Let's transform your online presence.",
        "stats": {
            "experience": "4+",
            "projects": "200+",
            "satisfaction": "98%"
        }
    },
    "about": {
        "title": "Passionate Digital Strategist & Developer",
        "description": [
            "With over 4+ years of experience in the digital landscape, I specialize in creating comprehensive solutions that drive real business results. My expertise spans across digital marketing, modern web development, and profitable e-commerce strategies.",
            "I believe in data-driven approaches, user-centric design, and cutting-edge technologies to deliver exceptional results for my clients. Every project is an opportunity to exceed expectations and build lasting partnerships."
        ]
    },
    "services": {
        "digital_marketing": {
            "title": "Digital Marketing",
            "description": "Strategic SEO, Google/Facebook Ads, content marketing, and analytics to boost your online presence."
        },
        "web_development": {
            "title": "Web Development", 
            "description": "Modern responsive websites, landing pages, speed optimization, and seamless integrations."
        },
        "shopify_dropshipping": {
            "title": "Shopify & Dropshipping",
            "description": "Complete store setup, product research, conversion optimization, and targeted advertising."
        }
    },
    "pricing": {
        "starter": {
            "price_monthly": 499,
            "price_yearly": 399,
            "features": [
                "Basic SEO Optimization",
                "Social Media Setup", 
                "Landing Page Design",
                "Monthly Analytics Report",
                "Email Support"
            ]
        },
        "pro": {
            "price_monthly": 999,
            "price_yearly": 799,
            "features": [
                "Advanced SEO & Content",
                "Google & Facebook Ads",
                "Custom Website Development", 
                "E-commerce Integration",
                "Weekly Performance Reviews",
                "Priority Support"
            ]
        },
        "elite": {
            "price_monthly": 1999,
            "price_yearly": 1599,
            "features": [
                "Complete Digital Strategy",
                "Multi-platform Ad Management",
                "Full-stack Web Solutions",
                "Shopify Store Management", 
                "24/7 Dedicated Support",
                "Monthly Strategy Calls"
            ]
        }
    },
    "testimonials": [
        {
            "name": "Sarah Johnson",
            "role": "CEO, TechStart Inc.",
            "text": "DMS MEHEDI transformed our online presence completely. Our website traffic increased by 400% and our conversion rates doubled within just 3 months. Exceptional work!",
            "rating": 5
        },
        {
            "name": "Michael Chen", 
            "role": "Founder, EcoProducts",
            "text": "The Shopify store he built for us generated over $100K in revenue in the first quarter. His expertise in dropshipping and conversion optimization is outstanding.",
            "rating": 5
        },
        {
            "name": "Emily Rodriguez",
            "role": "Marketing Director, GrowthCorp", 
            "text": "Professional, reliable, and results-driven. Our Google Ads campaigns now have a 300% ROI thanks to his strategic approach and continuous optimization.",
            "rating": 5
        }
    ],
    "contact": {
        "success_message": "Thanks for your message! We've received it and will reply within 24 hours. — DMS MEHEDI"
    }
}

def ensure_content_file():
    """Ensure content file exists with default content"""
    os.makedirs(os.path.dirname(CONTENT_FILE), exist_ok=True)
    if not os.path.exists(CONTENT_FILE):
        with open(CONTENT_FILE, 'w') as f:
            json.dump(DEFAULT_CONTENT, f, indent=2)

def load_content():
    """Load content from file"""
    ensure_content_file()
    try:
        with open(CONTENT_FILE, 'r') as f:
            return json.load(f)
    except:
        return DEFAULT_CONTENT

def save_content(content):
    """Save content to file"""
    ensure_content_file()
    try:
        with open(CONTENT_FILE, 'w') as f:
            json.dump(content, f, indent=2)
        return True
    except:
        return False

@cms_bp.route('/content', methods=['GET'])
def get_content():
    """Get all content"""
    content = load_content()
    return jsonify({
        'success': True,
        'content': content
    }), 200

@cms_bp.route('/content', methods=['PUT'])
def update_content():
    """Update content"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate required structure
        current_content = load_content()
        
        # Update only provided fields
        for section, section_data in data.items():
            if section in current_content:
                if isinstance(section_data, dict):
                    current_content[section].update(section_data)
                else:
                    current_content[section] = section_data
        
        if save_content(current_content):
            return jsonify({
                'success': True,
                'message': 'Content updated successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save content'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error updating content: {str(e)}'
        }), 500

@cms_bp.route('/content/<section>', methods=['GET'])
def get_content_section(section):
    """Get specific content section"""
    content = load_content()
    if section in content:
        return jsonify({
            'success': True,
            'content': content[section]
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': 'Section not found'
        }), 404

@cms_bp.route('/content/<section>', methods=['PUT'])
def update_content_section(section):
    """Update specific content section"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        content = load_content()
        content[section] = data
        
        if save_content(content):
            return jsonify({
                'success': True,
                'message': f'{section} updated successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save content'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error updating {section}: {str(e)}'
        }), 500

@cms_bp.route('/admin', methods=['GET'])
def admin_panel():
    """Simple admin panel for content management"""
    admin_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>DMS MEHEDI - Content Management</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
            .section { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
            .section h3 { color: #333; border-bottom: 2px solid #3b82f6; padding-bottom: 10px; }
            textarea, input { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; }
            textarea { height: 100px; resize: vertical; }
            button { background: #3b82f6; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #2563eb; }
            .success { color: green; margin: 10px 0; }
            .error { color: red; margin: 10px 0; }
            .form-group { margin-bottom: 15px; }
            label { display: block; font-weight: bold; margin-bottom: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>DMS MEHEDI - Content Management System</h1>
            <p>Use this panel to update website content. Changes will be reflected immediately on the live site.</p>
            
            <div id="message"></div>
            
            <div class="section">
                <h3>Hero Section</h3>
                <div class="form-group">
                    <label>Main Title:</label>
                    <input type="text" id="hero_title" placeholder="Hi, I'm DMS MEHEDI">
                </div>
                <div class="form-group">
                    <label>Description:</label>
                    <textarea id="hero_description" placeholder="I help businesses grow..."></textarea>
                </div>
                <button onclick="updateSection('hero')">Update Hero</button>
            </div>
            
            <div class="section">
                <h3>About Section</h3>
                <div class="form-group">
                    <label>Title:</label>
                    <input type="text" id="about_title" placeholder="Passionate Digital Strategist & Developer">
                </div>
                <div class="form-group">
                    <label>Description (separate paragraphs with ||):</label>
                    <textarea id="about_description" placeholder="Paragraph 1 || Paragraph 2"></textarea>
                </div>
                <button onclick="updateSection('about')">Update About</button>
            </div>
            
            <div class="section">
                <h3>Contact Success Message</h3>
                <div class="form-group">
                    <label>Success Message:</label>
                    <textarea id="contact_message" placeholder="Thanks for your message! We've received it..."></textarea>
                </div>
                <button onclick="updateSection('contact')">Update Contact</button>
            </div>
            
            <div class="section">
                <h3>Current Content (JSON)</h3>
                <textarea id="full_content" style="height: 300px;" readonly></textarea>
                <button onclick="loadContent()">Refresh Content</button>
            </div>
        </div>
        
        <script>
            function showMessage(text, isError = false) {
                const messageDiv = document.getElementById('message');
                messageDiv.innerHTML = `<div class="${isError ? 'error' : 'success'}">${text}</div>`;
                setTimeout(() => messageDiv.innerHTML = '', 5000);
            }
            
            function loadContent() {
                fetch('/api/content')
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            document.getElementById('full_content').value = JSON.stringify(data.content, null, 2);
                            
                            // Populate form fields
                            const content = data.content;
                            document.getElementById('hero_title').value = content.hero?.title || '';
                            document.getElementById('hero_description').value = content.hero?.description || '';
                            document.getElementById('about_title').value = content.about?.title || '';
                            document.getElementById('about_description').value = content.about?.description?.join(' || ') || '';
                            document.getElementById('contact_message').value = content.contact?.success_message || '';
                        }
                    })
                    .catch(error => showMessage('Error loading content: ' + error, true));
            }
            
            function updateSection(section) {
                let data = {};
                
                if (section === 'hero') {
                    data = {
                        title: document.getElementById('hero_title').value,
                        description: document.getElementById('hero_description').value
                    };
                } else if (section === 'about') {
                    const description = document.getElementById('about_description').value;
                    data = {
                        title: document.getElementById('about_title').value,
                        description: description.split(' || ').map(p => p.trim()).filter(p => p)
                    };
                } else if (section === 'contact') {
                    data = {
                        success_message: document.getElementById('contact_message').value
                    };
                }
                
                fetch(`/api/content/${section}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showMessage(data.message);
                        loadContent();
                    } else {
                        showMessage(data.error, true);
                    }
                })
                .catch(error => showMessage('Error updating content: ' + error, true));
            }
            
            // Load content on page load
            loadContent();
        </script>
    </body>
    </html>
    """
    return admin_html

