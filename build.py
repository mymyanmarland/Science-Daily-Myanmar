import os
import shutil
import math
import markdown
import json  # <--- ဒီတစ်ခု အသစ်တိုးလာပါတယ်
from jinja2 import Environment, FileSystemLoader
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

# --- CONFIGURATION ---
CONTENT_DIR = 'content'
OUTPUT_DIR = 'docs'
TEMPLATE_DIR = 'templates'
POSTS_PER_PAGE = 6

# --- SETUP JINJA2 ---
if not os.path.exists(TEMPLATE_DIR):
    print(f"❌ Error: '{TEMPLATE_DIR}' folder မရှိပါ။")
    exit()

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def clean_and_create_dir(path):
    print(f"   Using output directory: {path}")
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
        except Exception as e:
            print(f"❌ Error cleaning directory: {e}")
            return
            
    os.makedirs(path)
    os.makedirs(os.path.join(path, 'css'))
    os.makedirs(os.path.join(path, 'images'))

def generate_css_syntax_highlighting():
    print("   Generating Syntax Highlighter CSS...")
    formatter = HtmlFormatter(style='monokai')
    css_content = formatter.get_style_defs('.codehilite')
    with open(os.path.join(OUTPUT_DIR, 'css', 'syntax.css'), 'w') as f:
        f.write(css_content)

def parse_markdown_posts():
    print("   Parsing Markdown files...")
    posts = []
    md = markdown.Markdown(extensions=['meta', 'fenced_code', 'codehilite'])

    if not os.path.exists(CONTENT_DIR):
        print(f"❌ Error: '{CONTENT_DIR}' folder မရှိပါ။")
        return []

    files = [f for f in os.listdir(CONTENT_DIR) if f.endswith(".md")]
    if not files:
        print("⚠️ Warning: .md file တစ်ခုမှ မတွေ့ပါ။")
        return []

    for filename in files:
        filepath = os.path.join(CONTENT_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
            html = md.convert(text)
            
            word_count = len(text.split())
            read_time = round(word_count / 200)
            read_time = 1 if read_time < 1 else read_time
            
            if hasattr(md, 'Meta'):
                meta = {k: v[0] for k, v in md.Meta.items()}
            else:
                meta = {}
            
            if 'title' not in meta: meta['title'] = filename.replace('.md', '')
            if 'summary' not in meta: meta['summary'] = "No summary provided."
            if 'date' not in meta: meta['date'] = '2025-01-01'

            slug = filename.replace('.md', '.html')
            
            posts.append({
                'slug': slug,
                'html': html,
                'meta': meta,
                'filename': filename,
                'read_time': read_time
            })
            md.reset() 
    
    posts.sort(key=lambda x: x['meta']['date'], reverse=True)
    return posts

def build():
    print("🚀 Starting Build Process...")
    clean_and_create_dir(OUTPUT_DIR)
    
    src_img = os.path.join(CONTENT_DIR, 'images')
    if os.path.exists(src_img):
        print("   Copying images...")
        shutil.copytree(src_img, os.path.join(OUTPUT_DIR, 'images'), dirs_exist_ok=True)

    generate_css_syntax_highlighting()
    posts = parse_markdown_posts()
    
    if not posts:
        print("❌ No posts found. Exiting.")
        return

    # --- NEW: Generate Search Index JSON ---
    print("   Creating search index...")
    search_data = []
    for post in posts:
        search_data.append({
            "title": post['meta']['title'],
            "url": post['slug'],
            "summary": post['meta']['summary']
        })
    
    with open(os.path.join(OUTPUT_DIR, 'search.json'), 'w', encoding='utf-8') as f:
        json.dump(search_data, f)
    # ---------------------------------------

    print(f"   Generating HTML for {len(posts)} posts...")
    
    try:
        post_template = env.get_template('post.html')
        index_template = env.get_template('index.html')
    except Exception as e:
        print(f"❌ Template Error: {e}")
        return

    for post in posts:
        output_path = os.path.join(OUTPUT_DIR, post['slug'])
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(post_template.render(post=post, title=post['meta'].get('title')))
    
    total_posts = len(posts)
    total_pages = math.ceil(total_posts / POSTS_PER_PAGE)

    for page_num in range(1, total_pages + 1):
        start = (page_num - 1) * POSTS_PER_PAGE
        end = start + POSTS_PER_PAGE
        chunk = posts[start:end]
        
        filename = 'index.html' if page_num == 1 else f'page{page_num}.html'
        
        prev_url = ''
        next_url = ''
        if page_num > 1:
            prev_url = 'index.html' if page_num == 2 else f'page{page_num-1}.html'
        if page_num < total_pages:
            next_url = f'page{page_num+1}.html'

        with open(os.path.join(OUTPUT_DIR, filename), 'w', encoding='utf-8') as f:
            f.write(index_template.render(
                posts=chunk,
                current_page=page_num,
                total_pages=total_pages,
                prev_url=prev_url,
                next_url=next_url,
                title="Home"
            ))

    print(f"✅ Build Complete! Generated website in '{OUTPUT_DIR}/' folder.")

if __name__ == "__main__":
    build()