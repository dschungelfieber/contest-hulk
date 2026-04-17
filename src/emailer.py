from datetime import datetime
import html
from collections import defaultdict, Counter

CATEGORY_ICONS = {
    'automotive': '🚗', 'travel': '✈️', 'technology': '💻',
    'outdoor': '🏔️', 'home': '🏠', 'cash': '💵',
    'fitness': '💪', 'clothing': '👕', 'food_bev': '🍔',
    'casino': '🎰', 'experience': '🎟️', 'other': '🏆',
}

CATEGORY_COLORS = {
    'automotive': '#1a73e8', 'travel': '#0f9d58', 'technology': '#9c27b0',
    'outdoor': '#795548', 'home': '#ff9800', 'cash': '#4caf50',
    'fitness': '#f44336', 'clothing': '#e91e63', 'food_bev': '#ff5722',
    'casino': '#607d8b', 'experience': '#3f51b5', 'other': '#9e9e9e',
}

def format_prize(value):
    if value >= 1000000:
        return f"${value/1000000:.1f}M+"
    elif value >= 1000:
        return f"${value:,}"
    elif value > 0:
        return f"${value}"
    return ""

def age_badge(date):
    if not date:
        return '<span style="background:#757575;color:white;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600;">NEW FIND</span>'
    days = (datetime.now() - date).days
    if days <= 1:
        color, label = '#2e7d32', 'TODAY'
    elif days <= 3:
        color, label = '#388e3c', f'{days}d ago'
    elif days <= 7:
        color, label = '#f57c00', f'{days}d ago'
    else:
        color, label = '#757575', f'{days}d ago'
    return f'<span style="background:{color};color:white;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600;">{label}</span>'

def build_contest_card(contest):
    title = html.escape(contest.get('title', 'Untitled')[:80])
    url = contest.get('url', '#')
    desc = html.escape(contest.get('description', '')[:200])
    source = html.escape(contest.get('source', ''))
    category = contest.get('category', 'other')
    prize_val = contest.get('prize_value', 0)
    date = contest.get('date')
    icon = CATEGORY_ICONS.get(category, '🏆')
    color = CATEGORY_COLORS.get(category, '#9e9e9e')
    prize_str = format_prize(prize_val)
    badge = age_badge(date)
    prize_html = f'<span style="font-size:16px;font-weight:700;color:#2e7d32;">{prize_str}</span><br>' if prize_str else ''
    return f'''
    <div style="background:white;border-radius:10px;padding:16px;margin-bottom:12px;box-shadow:0 2px 6px rgba(0,0,0,0.08);border-left:4px solid {color};">
        <div style="margin-bottom:6px;">
            <span style="background:{color};color:white;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700;">{icon} {category.upper()}</span>
            &nbsp;{badge}
        </div>
        <h3 style="margin:6px 0;font-size:15px;font-weight:700;">
            <a href="{url}" style="color:#1a1a1a;text-decoration:none;">{title}</a>
        </h3>
        <p style="margin:0 0 8px;font-size:12px;color:#555;">{desc}</p>
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:11px;color:#888;">Source: {source}</span>
            <div>{prize_html}<a href="{url}" style="background:{color};color:white;padding:8px 16px;border-radius:6px;text-decoration:none;font-weight:700;font-size:12px;">ENTER NOW →</a></div>
        </div>
    </div>'''

def build_email(contests):
    now = datetime.now()
    date_str = now.strftime("%A, %B %d, %Y")
    count = len(contests)
    subject = f"Contest Hulk: {count} Fresh Sweepstakes - {now.strftime('%b %d')}"
    if not contests:
        return subject, f"<p>No new contests found today. The Hulk smashes again tomorrow.</p>"
    by_cat = defaultdict(list)
    for c in contests:
        by_cat[c.get('category', 'other')].append(c)
    sections = ''
    for cat in sorted(by_cat.keys(), key=lambda x: -len(by_cat[x])):
        cat_contests = by_cat[cat]
        icon = CATEGORY_ICONS.get(cat, '🏆')
        color = CATEGORY_COLORS.get(cat, '#9e9e9e')
        cards = ''.join(build_contest_card(c) for c in cat_contests)
        sections += f'<div style="margin-bottom:28px;"><h2 style="color:{color};border-bottom:3px solid {color};padding-bottom:6px;">{icon} {cat.upper().replace("_"," ")} ({len(cat_contests)})</h2>{cards}</div>'
    top_prizes = [c for c in contests if c.get('prize_value', 0) >= 5000]
    highlight = ''
    if top_prizes:
        items = ''.join(f'<li><strong>{format_prize(c["prize_value"])}</strong> — <a href="{c["url"]}">{html.escape(c["title"][:60])}</a></li>' for c in top_prizes[:5])
        highlight = f'<div style="background:#fff8e1;border:2px solid #ffc107;border-radius:10px;padding:14px;margin-bottom:20px;"><h3 style="margin:0 0 10px;color:#f57c00;">🌟 BIG PRIZES ($5,000+)</h3><ul>{items}</ul></div>'
    body = f'''<!DOCTYPE html><html><body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,sans-serif;">
    <div style="max-width:660px;margin:0 auto;padding:16px;">
        <div style="background:linear-gradient(135deg,#1a237e,#283593);border-radius:14px;padding:24px;margin-bottom:18px;text-align:center;">
            <div style="font-size:40px;">🏆💪</div>
            <h1 style="margin:6px 0;color:white;font-size:26px;">CONTEST HULK</h1>
            <p style="margin:4px 0;color:#90caf9;font-size:13px;">{date_str} | {count} Fresh Contests</p>
            <p style="margin:4px 0;color:#64b5f6;font-size:11px;">California Eligible · Email Entry · No Social Required</p>
        </div>
        {highlight}
        {sections}
        <div style="text-align:center;padding:16px;color:#999;font-size:11px;border-top:1px solid #e0e0e0;">
            <p>Contest Hulk · Built for Matty B · El Segundo, CA</p>
            <p>Always verify rules and eligibility at the source before entering.</p>
        </div>
    </div></body></html>'''
    return subject, body
