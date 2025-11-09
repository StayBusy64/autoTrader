# Enhanced Indicator Hierarchy Tree Visualization

## 📊 Overview
A beautiful, interactive web-based tool for organizing, searching, and managing your trading indicators and backtesting strategies.

## 🚀 Quick Start

### Method 1: Open Locally
1. Simply open `indicator_hierarchy_tree.html` in your web browser
2. The visualization will load automatically with the sample indicators

### Method 2: Run with Python HTTP Server
```bash
cd /home/user/autoTrader
python3 -m http.server 8000
```
Then open your browser to: `http://localhost:8000/indicator_hierarchy_tree.html`

## 📁 Files Included

- **indicator_hierarchy_tree.html** - The main visualization tool (52KB)
- **indicators_structure.json** - Sample indicator data (16KB)
- **INDICATOR_TREE_README.md** - This documentation

## 🎨 Features

### 🔍 Search & Filter
- **Real-time Search**: Search by name, author, or category
- **Advanced Filters**:
  - Filter by file type
  - Filter by author
  - Filter by version (has version / no version)
  - Date range filtering (modified after/before)
- **Search Highlighting**: Matching terms are highlighted in yellow

### 📂 Tree Navigation
- **Expand/Collapse**: Click categories to expand or collapse
- **Expand All / Collapse All**: Bulk operations for all categories
- **Auto-expand on Search**: Categories with matching results auto-expand
- **Persistent State**: Expansion state saved in browser localStorage

### ☑️ Multi-Select Mode
- Enable multi-select to choose multiple indicators
- Select entire categories at once
- Export only selected indicators

### 💾 Export Options
- **Export to JSON**: Download filtered or selected indicators as JSON
- **Export to CSV**: Download as CSV for Excel/spreadsheet analysis
- **Smart Export**: Exports selected items if any, otherwise exports filtered results

### 📊 Live Statistics
- Total indicators count
- Visible indicators (after filtering)
- Selected indicators count
- Number of categories

### 🎯 Interactive Tooltips
- Hover over any indicator to see detailed information:
  - Name and Title
  - Category and Type
  - Author and Version
  - Last Modified date
  - Full file path

### ⌨️ Keyboard Shortcuts
- **Ctrl/Cmd + F**: Focus search box
- **Ctrl/Cmd + E**: Expand all categories
- **Ctrl/Cmd + Shift + E**: Collapse all categories
- **Ctrl/Cmd + M**: Toggle multi-select mode

### 🎨 Beautiful UI
- Dark gradient background
- Neon glow effects
- Smooth animations
- Responsive design (works on mobile)
- Color-coded categories

## 📝 Customizing with Your Own Indicators

### Understanding the JSON Structure

The `indicators_structure.json` file contains an array of indicator objects. Each indicator has these fields:

```json
{
  "Name": "RSI",
  "Title": "Relative Strength Index",
  "Category": "Momentum Indicators",
  "FileType": "Python",
  "Version": "2.1",
  "Author": "J. Welles Wilder",
  "RelativePath": "indicators/momentum/rsi.py",
  "LastModified": "2025-02-10"
}
```

### Field Descriptions:
- **Name** (required): Short identifier for the indicator
- **Title** (optional): Full descriptive name
- **Category** (required): Grouping category (creates tree hierarchy)
- **FileType** (optional): File type (Python, Pine Script, etc.)
- **Version** (optional): Version number
- **Author** (optional): Creator/author name
- **RelativePath** (optional): Path to the file
- **LastModified** (optional): Last modification date (YYYY-MM-DD format)

### Creating Your Own Indicator List

#### Option 1: Manual JSON Creation
Edit `indicators_structure.json` directly with your indicators:

```json
[
  {
    "Name": "MyCustomIndicator",
    "Title": "My Custom Trading Indicator",
    "Category": "Custom Indicators",
    "FileType": "Python",
    "Version": "1.0",
    "Author": "Your Name",
    "RelativePath": "indicators/custom/my_indicator.py",
    "LastModified": "2025-11-09"
  }
]
```

#### Option 2: Python Script to Auto-Generate
Create a script to scan your indicator files and generate the JSON:

```python
import os
import json
from datetime import datetime

def scan_indicators(base_path):
    indicators = []

    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, base_path)

                # Extract metadata (you can parse the file for more info)
                stat = os.stat(full_path)
                modified = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d')

                # Determine category from directory structure
                parts = relative_path.split(os.sep)
                category = parts[0] if len(parts) > 1 else "Uncategorized"

                indicator = {
                    "Name": file.replace('.py', ''),
                    "Title": file.replace('.py', '').replace('_', ' ').title(),
                    "Category": category.replace('_', ' ').title(),
                    "FileType": "Python",
                    "RelativePath": relative_path,
                    "LastModified": modified
                }

                indicators.append(indicator)

    return indicators

# Usage
indicators = scan_indicators('/path/to/your/indicators')
with open('indicators_structure.json', 'w') as f:
    json.dump(indicators, f, indent=2)
```

#### Option 3: Parse Indicator Metadata from Files
If your indicators have docstrings or metadata, parse them:

```python
import re

def parse_indicator_metadata(file_path):
    """Extract metadata from indicator file docstrings"""
    with open(file_path, 'r') as f:
        content = f.read()

    # Extract from docstring
    metadata = {
        'Name': os.path.basename(file_path).replace('.py', ''),
        'FileType': 'Python'
    }

    # Parse version (e.g., # Version: 1.0)
    version_match = re.search(r'#\s*Version:\s*(\S+)', content)
    if version_match:
        metadata['Version'] = version_match.group(1)

    # Parse author (e.g., # Author: John Doe)
    author_match = re.search(r'#\s*Author:\s*(.+)', content)
    if author_match:
        metadata['Author'] = author_match.group(1).strip()

    # Parse description from docstring
    docstring_match = re.search(r'"""(.+?)"""', content, re.DOTALL)
    if docstring_match:
        metadata['Title'] = docstring_match.group(1).strip().split('\n')[0]

    return metadata
```

## 📚 Sample Categories Included

The example JSON includes these categories:
- **Trend Indicators**: MA, EMA, MACD, ADX, Parabolic SAR, Supertrend, Ichimoku
- **Momentum Indicators**: RSI, Stochastic, CCI, Williams %R, ROC, MFI, TSI
- **Volatility Indicators**: Bollinger Bands, ATR, Keltner Channels, Donchian, Standard Deviation
- **Volume Indicators**: OBV, VWAP, Accumulation/Distribution, Chaikin Money Flow, Volume Oscillator
- **Oscillators**: Awesome, Aroon, Detrended Price, Ultimate, Klinger
- **Support & Resistance**: Pivot Points, Fibonacci, SR Zones, Camarilla
- **Backtesting Strategies**: Mean Reversion, Trend Following, Breakout, RSI Divergence, Grid Trading, Scalping, ML-Based
- **Custom Hybrid Indicators**: Multi-Indicator Confluence, Volatility-Adjusted RSI, Smart Money Index, Adaptive EMA
- **Chart Patterns**: Heikin-Ashi, Renko, Harmonic Patterns, Elliott Wave
- **Risk Management**: Risk/Reward Calculator, Position Sizer, Drawdown Monitor, Kelly Criterion

Total: **56 sample indicators** across **10 categories**

## 🔧 Customization Options

### Changing Colors
Edit the CSS in the HTML file to change the color scheme:

```css
/* Main gradient background */
background: linear-gradient(135deg, #0a0e27 0%, #151932 50%, #0a0e27 100%);

/* Primary accent color (cyan) */
border-color: rgba(0, 255, 204, 0.5);

/* Secondary accent color (purple) */
background: linear-gradient(90deg, rgba(60, 20, 120, 0.8), rgba(80, 30, 150, 0.8));
```

### Adding More Metadata Fields
To add custom fields to indicators:

1. Add the field to your JSON objects
2. Update the tooltip display in the `showTooltip` function
3. Add to CSV export headers if needed

### Changing Auto-Expand Behavior
Find this code in the HTML to change how many categories auto-expand:

```javascript
// Auto-expand first 2 categories on initial load
setTimeout(() => {
    const firstCategories = document.querySelectorAll('.node.level-0');
    firstCategories.forEach((node, index) => {
        if (index < 2 && !state.expandedNodes.has(node.dataset.nodeId)) {
            toggleNode(node);
        }
    });
}, 100);
```

Change `index < 2` to expand more or fewer categories.

## 💡 Pro Tips

1. **Large Indicator Libraries**: The tool handles thousands of indicators efficiently
2. **Backup**: Export your current view as JSON to save filtered subsets
3. **Search Operators**: Search terms are case-insensitive and match partial strings
4. **Browser Compatibility**: Works best in Chrome, Firefox, Safari, Edge (modern browsers)
5. **Mobile Usage**: Fully responsive - works on tablets and phones
6. **Offline**: Works completely offline once loaded (no internet required)
7. **Data Privacy**: All data stays in your browser - nothing sent to any server

## 🐛 Troubleshooting

### Issue: "Error Loading Indicators"
- **Solution**: Ensure `indicators_structure.json` is in the same directory as the HTML file
- Check that the JSON file is valid (use jsonlint.com to validate)

### Issue: Filters Not Working
- **Solution**: Click "Clear Filters" and try again
- Clear browser localStorage if needed

### Issue: Search Not Highlighting
- **Solution**: Refresh the page
- Check that you're typing in the search box (not the filter dropdowns)

### Issue: Export Not Working
- **Solution**: Check browser download settings
- Try a different browser
- Ensure pop-up blocker isn't blocking downloads

## 🔄 Updating the Visualization

To use a newer version:
1. Backup your `indicators_structure.json` file
2. Replace the HTML file with the new version
3. Your data will still work (JSON structure is backward compatible)

## 📖 Integration Ideas

### With Trading Platforms
- Export indicator lists to CSV for documentation
- Use JSON export to backup your indicator library
- Create multiple JSON files for different strategies

### With Version Control
- Track changes to indicators using git diff on JSON files
- See when indicators were last updated
- Share indicator libraries with your team

### With Backtesting Tools
- Filter indicators by performance
- Track version updates of profitable indicators
- Organize by strategy type

## 🎯 Next Steps

1. **Replace sample data** with your actual indicators
2. **Customize categories** to match your workflow
3. **Add metadata** like performance metrics or notes
4. **Export** your organized library
5. **Share** the HTML with your team (just send both files)

## 🤝 Support

If you need help customizing this tool or adding features, you can:
- Modify the HTML directly (it's self-contained)
- Use browser DevTools to inspect and customize
- Create additional JSON files for different indicator sets

## 📜 License

This is a standalone tool - feel free to modify and use as needed for your trading workflow.

---

**Happy Trading! 📈**
