#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批量更新模板：添加 theme.css 引用，移除与 theme.css 冲突的浅色 :root 覆盖"""
import sys, os, re

templates_dir = r'D:\zhousirui\新建文件夹 (2)\mianshiguan\templates'

def has_light_override(content):
    """Check if :root defines light colors that conflict with dark theme.css"""
    # Look for specific light theme patterns in :root blocks
    patterns = [
        r'--bg-primary\s*:\s*#[Ff]8[A-Fa-f0-9]{4}',  # #F8FAFC
        r'--bg-secondary\s*:\s*#[Ff]{6}',              # #FFFFFF
        r'--bg-sidebar\s*:\s*#[Ff]1',                  # #F1F5F9
        r'--text-primary\s*:\s*#[1e]',                 # #1E293B
    ]
    for p in patterns:
        if re.search(p, content):
            return True
    return False

def add_theme_link(content):
    if '/static/css/theme.css' in content:
        return content
    # Add after <title> tag
    content = content.replace('</title>', '</title>\n    <link rel="stylesheet" href="/static/css/theme.css">', 1)
    return content

def remove_light_root_block(content):
    """Remove entire :root block if it contains light theme overrides"""
    pattern = r':root\s*\{[^}]*\}'

    def replacer(match):
        block = match.group(0)
        if has_light_override(block):
            return ''  # Remove it
        return block  # Keep it

    return re.sub(pattern, replacer, content)

for f in sorted(os.listdir(templates_dir)):
    if not f.endswith('.html'):
        continue
    fp = os.path.join(templates_dir, f)
    with open(fp, 'r', encoding='utf-8') as fh:
        content = fh.read()

    changed = False

    # Only add theme.css link to standalone templates
    if '{% extends' not in content:
        new_content = add_theme_link(content)
        if new_content != content:
            changed = True
            content = new_content

    # Remove light theme :root overrides (both extended and standalone)
    new_content = remove_light_root_block(content)
    if new_content != content:
        changed = True
        content = new_content

    if changed:
        with open(fp, 'w', encoding='utf-8') as fh:
            fh.write(content)
        print(f'  FIXED {f}')
    else:
        print(f'  OK    {f}')

print('\nDone!')
