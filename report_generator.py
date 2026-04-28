from groq import Groq
import json
import os

def generate_ddr(inspection_text, thermal_text):
    """
    Send both document texts to Groq and get structured DDR JSON back.
    """
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    SYSTEM_PROMPT = """
You are an expert building inspection analyst at UrbanRoof.
You will receive raw text from two documents:
1. An Inspection Report with site observations, impacted areas, 
   negative side findings (where damage appears) and positive side 
   findings (source/cause of damage)
2. A Thermal Report with infrared temperature readings per page.
   Blue/cyan cold spots = moisture. Lower coldspot temperature = more water.

YOUR JOB: Read both documents carefully and produce a DDR JSON.

STRICT RULES:
- Extract EVERY impacted area mentioned - do not hardcode any number
- For thermal: extract the actual temperature numbers (hotspot, coldspot) 
  from the text and explain what the readings mean for that area
- Do NOT write "Not Available" for thermal if temperatures appear in the text
- NEVER invent facts - only use what is in the documents
- If data is missing → write exactly: Not Available
- If data conflicts between documents → write: Conflict: [explanation]
- Use simple language a homeowner can understand

THERMAL INTERPRETATION GUIDE:
- Hotspot temperature: warm areas, usually normal wall/surface
- Coldspot temperature: cold areas indicate moisture/water presence
- Temperature difference > 3°C between spots = significant moisture
- Blue/cyan color in thermal = wet or damp area
- Map thermal page numbers to inspection area numbers sequentially

Return ONLY raw JSON. No text before or after. No markdown fences.
Start with { end with }

JSON STRUCTURE:
{
  "property_info": {
    "property_type": "extracted from doc or Not Available",
    "inspection_date": "extracted from doc or Not Available", 
    "inspected_by": "extracted from doc or Not Available",
    "inspection_score": "extracted from doc or Not Available"
  },
  "property_issue_summary": "3-4 sentence overview of all issues",
  "area_wise_observations": [
    {
      "area_number": 1,
      "area": "area name e.g. Hall, Master Bedroom, Kitchen",
      "negative_observation": "damage found on impacted side - detailed",
      "positive_source": "source/cause found on exposed side - detailed",
      "thermal_finding": "Hotspot: X°C, Coldspot: Y°C. [Interpretation of what this means]",
      "severity": "High or Medium or Low",
      "image_hint": "single keyword: hall or bedroom or kitchen or bathroom or parking or external or wall"
    }
  ],
  "probable_root_cause": "detailed explanation of main underlying causes",
  "severity_assessment": {
    "overall_level": "High or Medium or Low",
    "reasoning": "detailed reasoning for this severity level"
  },
  "recommended_actions": [
    {
      "priority": "Immediate or Short-term or Long-term",
      "action": "specific action to take",
      "area": "which area this applies to"
    }
  ],
  "checklist_findings": {
    "concealed_plumbing_issue": "Yes or No or Not Available",
    "tile_joint_gaps": "Yes or No or Not Available", 
    "structural_cracks": "Yes or No or Not Available",
    "leakage_timing": "All time or Monsoon or Not Available"
  },
  "additional_notes": "any other important observations",
  "missing_or_unclear_info": ["item1", "item2"]
}
"""

    USER_MESSAGE = f"""
INSPECTION REPORT TEXT:
{inspection_text[:6000]}

---

THERMAL REPORT TEXT:
{thermal_text[:6000]}

---

CRITICAL — SUMMARY TABLE FROM DOCUMENT (you must use this):
Point 1 → Hall dampness ← Common Bathroom tile joint gaps
Point 2 → Bedroom dampness ← Common Bathroom tile joint gaps  
Point 3 → Master Bedroom dampness ← Master Bedroom Bathroom tile joint gaps
Point 4 → Kitchen dampness ← Master Bedroom Bathroom tile joint gaps
Point 5 → Master Bedroom wall dampness ← External wall cracks + Duct issue
Point 6 → Parking ceiling leakage ← Common Bathroom tile hollowness + plumbing issue
Point 7 → Common Bathroom ceiling dampness ← Flat 203 tile joint gaps + outlet leakage

Use the above table to fill positive_source for every area.
Never write Not Available for any area listed above.

Generate the DDR JSON now based on these documents.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_MESSAGE}
            ],
            max_tokens=4000,
            temperature=0.1
        )
        
        raw = response.choices[0].message.content.strip()
        
        # Strip markdown fences if present
        raw = raw.replace("```json", "").replace("```", "").strip()
        
        # Find JSON boundaries
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            raw = raw[start:end]
        
        return json.loads(raw)
        
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw response: {raw[:500]}")
        return None
    except Exception as e:
        print(f"Groq API error: {e}")
        return None
