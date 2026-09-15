import os

STATIC_IMG_DIR = os.path.join(os.path.dirname(__file__), "static", "img")
os.makedirs(STATIC_IMG_DIR, exist_ok=True)

players_data = [
    {"file": "sample_player_1.svg", "name": "M. Sterling", "num": "1", "pos": "GK", "bg": "#1E293B", "accent": "#0EA5E9"},
    {"file": "sample_player_2.svg", "name": "A. Kumar", "num": "10", "pos": "CM", "bg": "#0F172A", "accent": "#16A34A"},
    {"file": "sample_player_3.svg", "name": "D. Vance", "num": "9", "pos": "ST", "bg": "#18181B", "accent": "#E11D48"},
    {"file": "sample_player_4.svg", "name": "L. Silva", "num": "4", "pos": "CB", "bg": "#111827", "accent": "#3B82F6"},
    {"file": "sample_player_5.svg", "name": "V. Patel", "num": "6", "pos": "CDM", "bg": "#172554", "accent": "#EAB308"},
    {"file": "sample_player_6.svg", "name": "M. Rossi", "num": "7", "pos": "LW", "bg": "#2A1215", "accent": "#F97316"},
    {"file": "sample_player_7.svg", "name": "R. Singh", "num": "10", "pos": "RB", "bg": "#1E1B4B", "accent": "#A855F7"}
]

svg_template = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 400" width="300" height="400">
  <defs>
    <linearGradient id="bgGrad_{num}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{bg}"/>
      <stop offset="100%" stop-color="#050505"/>
    </linearGradient>
    <radialGradient id="spotlight_{num}" cx="50%" cy="30%" r="60%">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="{accent}" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <!-- Background -->
  <rect width="300" height="400" fill="url(#bgGrad_{num})"/>
  <rect width="300" height="400" fill="url(#spotlight_{num})"/>
  
  <!-- Subtle Grid Lines -->
  <path d="M0 100 H300 M0 200 H300 M0 300 H300 M100 0 V400 M200 0 V400" stroke="#FFFFFF" stroke-opacity="0.03" stroke-width="1"/>

  <!-- Jersey Badge Background Number -->
  <text x="150" y="220" font-family="Impact, sans-serif" font-size="160" font-weight="900" fill="{accent}" fill-opacity="0.08" text-anchor="middle">{num}</text>

  <!-- Player Silhouette -->
  <!-- Head -->
  <circle cx="150" cy="115" r="42" fill="#262626" stroke="{accent}" stroke-width="2"/>
  <path d="M 125 110 Q 150 85 175 110 Q 165 95 150 95 Q 135 95 125 110 Z" fill="#171717"/>
  
  <!-- Shoulders & Jersey -->
  <path d="M 75 290 Q 75 190 115 170 Q 150 160 185 170 Q 225 190 225 290 Z" fill="#141414" stroke="{accent}" stroke-width="2"/>
  
  <!-- Jersey Collar -->
  <path d="M 130 170 Q 150 195 170 170" fill="none" stroke="{accent}" stroke-width="3"/>
  
  <!-- DCF Logo Badge on Chest -->
  <circle cx="120" cy="205" r="10" fill="#0A0A0A" stroke="{accent}" stroke-width="1.5"/>
  <text x="120" y="208" font-family="sans-serif" font-size="6" font-weight="bold" fill="#FFFFFF" text-anchor="middle">DCF</text>

  <!-- Jersey Number on Chest -->
  <text x="150" y="260" font-family="Arial Black, sans-serif" font-size="52" font-weight="900" fill="#FFFFFF" text-anchor="middle">{num}</text>

  <!-- Bottom Dark Gradient Overlay -->
  <rect y="310" width="300" height="90" fill="url(#bgGrad_{num})"/>

  <!-- Name & Position Ribbon -->
  <rect x="20" y="340" width="260" height="42" fill="#0D0D0D" stroke="{accent}" stroke-width="1.5" rx="4"/>
  <text x="35" y="367" font-family="Arial Black, sans-serif" font-size="18" font-weight="bold" fill="#FFFFFF">{name}</text>
  <rect x="210" y="348" width="60" height="26" fill="{accent}" rx="3"/>
  <text x="240" y="366" font-family="Arial Black, sans-serif" font-size="13" font-weight="bold" fill="#FFFFFF" text-anchor="middle">{pos}</text>
</svg>"""

for p in players_data:
    content = svg_template.format(
        num=p["num"],
        name=p["name"],
        pos=p["pos"],
        bg=p["bg"],
        accent=p["accent"]
    )
    with open(os.path.join(STATIC_IMG_DIR, p["file"]), "w", encoding="utf-8") as f:
        f.write(content)

print("Generated sample player SVG avatars successfully!")
