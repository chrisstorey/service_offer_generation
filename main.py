import uuid
import random
import json
from datetime import datetime, timedelta


def generate_uuid():
    return str(uuid.uuid4())


# --- 1. Define Organizations ---
organizations = {
    "kirklees_council": {
        "id": generate_uuid(),
        "name": "Kirklees Council Employment & Skills",
        "description": "The local government team dedicated to supporting residents with employment, skills development, and career progression across Kirklees.",
        "url": "https://www.kirklees.gov.uk/employment-skills",
        "contact_phone": "01484 221000"
    },
    "wakefield_council": {
        "id": generate_uuid(),
        "name": "Wakefield Council Employment Hub",
        "description": "The local authority's dedicated service supporting residents into employment, training, and skills development across the Wakefield district.",
        "url": "https://www.wakefield.gov.uk/jobs-and-training",
        "contact_phone": "0345 8506506"
    },
    "jp_huddersfield": {
        "id": generate_uuid(),
        "name": "Jobcentre Plus Huddersfield",
        "description": "A government agency responsible for helping people find employment and providing support for those claiming benefits in Huddersfield and surrounding areas.",
        "url": "https://www.gov.uk/contact-jobcentre-plus",
        "contact_phone": "0800 169 0190"
    },
    "jp_wakefield": {
        "id": generate_uuid(),
        "name": "Jobcentre Plus Wakefield",
        "description": "A government agency responsible for helping people find employment and providing support for those claiming benefits in Wakefield and surrounding areas.",
        "url": "https://www.gov.uk/contact-jobcentre-plus",
        "contact_phone": "0800 169 0190"
    },
    "kirklees_college": {
        "id": generate_uuid(),
        "name": "Kirklees College",
        "description": "A large further education college with campuses across Kirklees, offering a wide range of vocational and academic courses, including ESOL and employment-focused training.",
        "url": "https://www.kirkleescollege.ac.uk/",
        "contact_phone": "01484 437000"
    },
    "wakefield_college": {
        "id": generate_uuid(),
        "name": "Heart of Yorkshire Education Group (Wakefield College)",
        "description": "Comprising Wakefield College, Selby College, and Castleford College, offering a wide range of education and apprenticeship programmes in the Wakefield district.",
        "url": "https://www.wakefield.ac.uk/",
        "contact_phone": "01924 789789"
    },
    "citizens_advice_kirklees": {
        "id": generate_uuid(),
        "name": "Citizens Advice Kirklees",
        "description": "Provides free, confidential, and impartial advice on a wide range of issues, including debt, benefits, employment, and housing, to residents of Kirklees.",
        "url": "https://www.citizensadvicekirklees.org.uk/",
        "contact_phone": "0808 278 7898"
    },
    "citizens_advice_wakefield": {
        "id": generate_uuid(),
        "name": "Citizens Advice Wakefield District",
        "description": "Provides free, confidential, and impartial advice on a wide range of issues, including debt, benefits, employment, and housing, to residents of the Wakefield district.",
        "url": "https://www.citizensadvice.org.uk/local/wakefield-district/",
        "contact_phone": "0808 278 7899"
    },
    "the_welcome_centre_hudd": {
        "id": generate_uuid(),
        "name": "The Welcome Centre (Huddersfield Foodbank)",
        "description": "A local charity providing food, toiletries, and other essential items to people in crisis in Huddersfield, often linked with employment support.",
        "url": "https://www.thewelcomecentre.org/",
        "contact_phone": "01484 515086"
    },
    "wakefield_foodbank": {
        "id": generate_uuid(),
        "name": "Wakefield Foodbank (The Trussell Trust)",
        "description": "Part of the Trussell Trust network, providing emergency food and support to local people in crisis across the Wakefield district.",
        "url": "https://wakefield.foodbank.org.uk/",
        "contact_phone": "07582 195431"
    },
    "kirklees_health_alliance": {
        "id": generate_uuid(),
        "name": "Kirklees Health Alliance",
        "description": "A collaborative of local health and social care providers focusing on long-term condition management and wellbeing.",
        "url": "https://www.kirkleeshealthalliance.org.uk/",
        "contact_phone": "01484 765432"
    },
    "wakefield_wellbeing_hub": {
        "id": generate_uuid(),
        "name": "Wakefield Wellbeing Hub",
        "description": "A comprehensive service offering support for mental and physical health, including self-management programs for long-term conditions.",
        "url": "https://www.wakefieldwellbeinghub.org.uk/",
        "contact_phone": "01924 112233"
    },
    "kirklees_childrens_centre": {
        "id": generate_uuid(),
        "name": "Kirklees Children's Centres",
        "description": "A network of local hubs offering services and support for families with young children, including childcare advice and activities.",
        "url": "https://www.kirklees.gov.uk/childrenscentres",
        "contact_phone": "01484 414887"
    },
    "wakefield_family_support": {
        "id": generate_uuid(),
        "name": "Wakefield Family Support Network",
        "description": "A charity dedicated to supporting families, offering parenting workshops, childcare advice, and children's activities.",
        "url": "https://www.wakefieldfamilysupport.org.uk/",
        "contact_phone": "01924 987654"
    },
    "community_action_hudd": {
        "id": generate_uuid(),
        "name": "Community Action Huddersfield",
        "description": "Facilitates and supports a wide range of community-led initiatives and provides space for local groups.",
        "url": "https://www.communityactionhudd.org.uk/",
        "contact_phone": "01484 554433"
    },
    "wakefield_community_link": {
        "id": generate_uuid(),
        "name": "Wakefield Community Link",
        "description": "Connects residents with local services, groups, and volunteering opportunities, managing several community venues.",
        "url": "https://www.wakefieldcommunitylink.org.uk/",
        "contact_phone": "01924 221100"
    },
    "scouts_kirklees": {
        "id": generate_uuid(),
        "name": "Kirklees Scouts District",
        "description": "The local scouting association, often with halls available for community use and various youth development programmes.",
        "url": "https://www.kirkleesscouts.org.uk/",
        "contact_phone": "01484 123456"
    },
    "scouts_wakefield": {
        "id": generate_uuid(),
        "name": "Wakefield District Scouts",
        "description": "The local scouting association in Wakefield, managing various Scout HQs used for youth and community activities.",
        "url": "https://www.wakefieldscouts.org.uk/",
        "contact_phone": "01924 654321"
    },
    "church_halls_kirklees": {
        "id": generate_uuid(),
        "name": "Kirklees Churches Together (Community Hubs)",
        "description": "A network of church halls across Kirklees offering space and support for community activities.",
        "url": "https://www.kirkleeschurches.org.uk/community",
        "contact_phone": "01484 998877"
    },
    "church_halls_wakefield": {
        "id": generate_uuid(),
        "name": "Wakefield Churches Community Network",
        "description": "Churches collaborating to provide community support, including hall access for local groups and services.",
        "url": "https://www.wakefieldchurches.org.uk/community",
        "contact_phone": "01924 776655"
    }
}

# --- 2. Define Locations ---
locations = {
    # Huddersfield & Kirklees Main Hubs
    "hudd_lib": {
        "id": generate_uuid(), "name": "Huddersfield Library & Information Centre",
        "address_1": "Princess Alexandra Walk", "city": "Huddersfield", "postal_code": "HD1 2SU", "latitude": 53.6477,
        "longitude": -1.7828,
        "accessibility": ["wheelchair_accessible", "accessible_toilet", "lift_access"]
    },
    "hudd_jcp": {
        "id": generate_uuid(), "name": "Huddersfield Jobcentre Plus",
        "address_1": "Castlegate", "city": "Huddersfield", "postal_code": "HD1 6BY", "latitude": 53.6480,
        "longitude": -1.7850,
        "accessibility": ["wheelchair_accessible", "accessible_toilet"]
    },
    "kirklees_college_hudd": {
        "id": generate_uuid(), "name": "Kirklees College - Huddersfield Centre",
        "address_1": "Waterfront Quarter, Manchester Road", "city": "Huddersfield", "postal_code": "HD1 3LF",
        "latitude": 53.6495, "longitude": -1.7760,
        "accessibility": ["wheelchair_accessible", "lift_access", "accessible_toilet"]
    },
    "hudd_citizens_advice": {
        "id": generate_uuid(), "name": "Citizens Advice Kirklees (Huddersfield Office)",
        "address_1": "30 John William Street", "city": "Huddersfield", "postal_code": "HD1 1BA", "latitude": 53.6450,
        "longitude": -1.7840,
        "accessibility": ["wheelchair_accessible", "accessible_toilet"]
    },
    "hudd_welcome_centre_loc": {
        "id": generate_uuid(), "name": "The Welcome Centre (Huddersfield)",
        "address_1": "15 Lord Street", "city": "Huddersfield", "postal_code": "HD1 1QB", "latitude": 53.6460,
        "longitude": -1.7835,
        "accessibility": ["wheelchair_accessible"]
    },
    "hudd_community_hub_central": {
        "id": generate_uuid(), "name": "Huddersfield Central Community Hub",
        "address_1": "Byram Street", "city": "Huddersfield", "postal_code": "HD1 1JF", "latitude": 53.6445,
        "longitude": -1.7810,
        "accessibility": ["wheelchair_accessible", "lift_access"]
    },
    "st_pauls_church_hudd": {
        "id": generate_uuid(), "name": "St. Paul's Church Hall (Huddersfield)",
        "address_1": "Queen Street", "city": "Huddersfield", "postal_code": "HD1 2SW", "latitude": 53.6480,
        "longitude": -1.7820,
        "accessibility": ["wheelchair_accessible"]
    },
    "kirkheaton_scout_hq": {
        "id": generate_uuid(), "name": "Kirkheaton Scout HQ",
        "address_1": "51 Moorside Road, Kirkheaton", "city": "Huddersfield", "postal_code": "HD5 0LR",
        "latitude": 53.6250, "longitude": -1.7200,
        "accessibility": ["parking_available"]
    },
    "dewsbury_lib": {
        "id": generate_uuid(), "name": "Dewsbury Library",
        "address_1": "Peace Museum, Wellington Rd", "city": "Dewsbury", "postal_code": "WF13 1DW", "latitude": 53.6890,
        "longitude": -1.6310,
        "accessibility": ["wheelchair_accessible", "accessible_toilet", "lift_access"]
    },
    "batley_community_centre": {
        "id": generate_uuid(), "name": "Batley Community Centre",
        "address_1": "Upper Commercial Street", "city": "Batley", "postal_code": "WF17 5EE", "latitude": 53.7120,
        "longitude": -1.6010,
        "accessibility": ["wheelchair_accessible", "parking_available"]
    },
    "mirfield_methodist_hall": {
        "id": generate_uuid(), "name": "Mirfield Methodist Church Hall",
        "address_1": "Doctor Lane", "city": "Mirfield", "postal_code": "WF14 8BT", "latitude": 53.6700,
        "longitude": -1.7000,
        "accessibility": ["wheelchair_accessible"]
    },
    "holmfirth_civic_hall": {
        "id": generate_uuid(), "name": "Holmfirth Civic Hall",
        "address_1": "Huddersfield Road", "city": "Holmfirth", "postal_code": "HD9 3AS", "latitude": 53.5780,
        "longitude": -1.7770,
        "accessibility": ["wheelchair_accessible", "parking_available"]
    },
    "gp_hudd_central": {
        "id": generate_uuid(), "name": "Huddersfield Central Medical Centre",
        "address_1": "New North Road", "city": "Huddersfield", "postal_code": "HD1 5AD", "latitude": 53.6490,
        "longitude": -1.7870,
        "accessibility": ["wheelchair_accessible", "accessible_toilet"]
    },
    "st_pauls_dewsbury_church": {
        "id": generate_uuid(), "name": "St. Paul's Church Hall (Dewsbury)",
        "address_1": "St Paul's Drive", "city": "Dewsbury", "postal_code": "WF13 2QW", "latitude": 53.6820,
        "longitude": -1.6250,
        "accessibility": ["wheelchair_accessible", "parking_available"]
    },
    "batley_jcp_outreach": {
        "id": generate_uuid(), "name": "Batley Jobcentre Plus Outreach",
        "address_1": "Wellington Street", "city": "Batley", "postal_code": "WF17 5EG", "latitude": 53.7070,
        "longitude": -1.6090,
        "accessibility": ["wheelchair_accessible"]
    },

    # Wakefield & District Main Hubs
    "wake_one": {
        "id": generate_uuid(), "name": "Wakefield One (Wakefield Council)",
        "address_1": "Burton Street", "city": "Wakefield", "postal_code": "WF1 2DA", "latitude": 53.6820,
        "longitude": -1.4990,
        "accessibility": ["wheelchair_accessible", "accessible_toilet", "lift_access", "parking_available"]
    },
    "wake_jcp": {
        "id": generate_uuid(), "name": "Wakefield Jobcentre Plus",
        "address_1": "Northgate", "city": "Wakefield", "postal_code": "WF1 3AZ", "latitude": 53.6840,
        "longitude": -1.4930,
        "accessibility": ["wheelchair_accessible", "accessible_toilet"]
    },
    "wakefield_college_city": {
        "id": generate_uuid(), "name": "Wakefield College City Campus",
        "address_1": "Margaret Street", "city": "Wakefield", "postal_code": "WF1 2DH", "latitude": 53.6780,
        "longitude": -1.4980,
        "accessibility": ["wheelchair_accessible", "parking_available", "lift_access"]
    },
    "wake_citizens_advice": {
        "id": generate_uuid(), "name": "Citizens Advice Wakefield Office",
        "address_1": "37 King Street", "city": "Wakefield", "postal_code": "WF1 2SR", "latitude": 53.6800,
        "longitude": -1.4940,
        "accessibility": ["wheelchair_accessible", "accessible_toilet"]
    },
    "wakefield_foodbank_main": {
        "id": generate_uuid(), "name": "Wakefield Foodbank Main Centre",
        "address_1": "Unit 2, Phoenix Court, Denby Dale Road", "city": "Wakefield", "postal_code": "WF2 7AN",
        "latitude": 53.6650, "longitude": -1.5050,
        "accessibility": ["wheelchair_accessible", "parking_available"]
    },
    "eastmoor_community_centre": {
        "id": generate_uuid(), "name": "Eastmoor Community Centre (Wakefield)",
        "address_1": "Eastmoor Drive", "city": "Wakefield", "postal_code": "WF1 4RT", "latitude": 53.6705,
        "longitude": -1.4705,
        "accessibility": ["wheelchair_accessible", "parking_available", "accessible_toilet"]
    },
    "wakefield_cathedral_loc": {
        "id": generate_uuid(), "name": "Wakefield Cathedral (Chapter House)",
        "address_1": "Cathedral Close", "city": "Wakefield", "postal_code": "WF1 2EF", "latitude": 53.6820,
        "longitude": -1.4970,
        "accessibility": ["wheelchair_accessible", "accessible_toilet"]
    },
    "sandal_scout_hq": {
        "id": generate_uuid(), "name": "Sandal Scout HQ",
        "address_1": "Behind Sandal Methodist Church, Barnsley Road", "city": "Wakefield", "postal_code": "WF1 5NU",
        "latitude": 53.6490, "longitude": -1.4900,
        "accessibility": ["parking_available"]
    },
    "castleford_lib": {
        "id": generate_uuid(), "name": "Castleford Library",
        "address_1": "Carlton Street", "city": "Castleford", "postal_code": "WF10 1EB", "latitude": 53.7270,
        "longitude": -1.3530,
        "accessibility": ["wheelchair_accessible", "accessible_toilet"]
    },
    "pontefract_lib": {
        "id": generate_uuid(), "name": "Pontefract Library",
        "address_1": "Salter Row", "city": "Pontefract", "postal_code": "WF8 1BE", "latitude": 53.6930,
        "longitude": -1.3120,
        "accessibility": ["wheelchair_accessible", "accessible_toilet"]
    },
    "ossett_town_hall": {
        "id": generate_uuid(), "name": "Ossett Town Hall Community Rooms",
        "address_1": "Market Place", "city": "Ossett", "postal_code": "WF5 8BE", "latitude": 53.6490,
        "longitude": -1.5640,
        "accessibility": ["wheelchair_accessible", "lift_access"]
    },
    "ackworth_village_hall": {
        "id": generate_uuid(), "name": "Ackworth Village Hall",
        "address_1": "Station Road, Ackworth", "city": "Pontefract", "postal_code": "WF7 7EL", "latitude": 53.6300,
        "longitude": -1.3000,
        "accessibility": ["wheelchair_accessible", "parking_available"]
    },
    "featherstone_community_centre": {
        "id": generate_uuid(), "name": "Featherstone Community Centre",
        "address_1": "Pontefract Road", "city": "Featherstone", "postal_code": "WF7 5AD", "latitude": 53.6700,
        "longitude": -1.3450,
        "accessibility": ["wheelchair_accessible", "parking_available"]
    },
    "gp_wake_north": {
        "id": generate_uuid(), "name": "Northgate Medical Centre (Wakefield)",
        "address_1": "Northgate", "city": "Wakefield", "postal_code": "WF1 3AD", "latitude": 53.6845,
        "longitude": -1.4920,
        "accessibility": ["wheelchair_accessible", "accessible_toilet"]
    },
    "wakefield_city_church": {
        "id": generate_uuid(), "name": "Wakefield City Church Community Hall",
        "address_1": "Elm Tree Street", "city": "Wakefield", "postal_code": "WF1 5AA", "latitude": 53.6850,
        "longitude": -1.4900,
        "accessibility": ["wheelchair_accessible", "parking_available"]
    }
}

# --- 3. Define Service Types and Descriptions ---
service_types = [
    {"name": "CV Writing Workshop",
     "description": "An interactive workshop to help you create a professional and impactful CV that stands out to employers.",
     "type": "training", "remote_chance": 0.5, "in_person_chance": 1.0},
    {"name": "Interview Skills Coaching",
     "description": "One-to-one coaching sessions to improve your interview techniques, build confidence, and prepare for common interview questions, including virtual interview etiquette.",
     "type": "counseling", "remote_chance": 0.8, "in_person_chance": 1.0},
    {"name": "Job Search Support Group",
     "description": "A weekly peer support group offering encouragement, sharing of job market insights, and practical job search strategies in a friendly, supportive environment.",
     "type": "peer_support", "remote_chance": 0.3, "in_person_chance": 1.0},
    {"name": "Digital Skills Training for Employment",
     "description": "Courses covering essential digital skills, including Microsoft Office, online applications, email communication, and cyber safety, to enhance employability in today's job market.",
     "type": "training", "remote_chance": 0.7, "in_person_chance": 1.0},
    {"name": "Career Guidance and Planning",
     "description": "Personalised one-to-one sessions with a qualified career advisor to explore career options, set realistic goals, and develop a strategic career plan tailored to individual aspirations and skills.",
     "type": "counseling", "remote_chance": 0.9, "in_person_chance": 1.0},
    {"name": "Apprenticeship Matching Service",
     "description": "Connects unemployed individuals with local apprenticeship opportunities and provides tailored support with applications, including interview preparation.",
     "type": "employment_support", "remote_chance": 0.6, "in_person_chance": 1.0},
    {"name": "Mental Health Support for Job Seekers",
     "description": "Confidential counselling, one-to-one support, and therapeutic group work for individuals experiencing mental health challenges, anxiety, or low mood while unemployed and seeking work.",
     "type": "health", "remote_chance": 0.9, "in_person_chance": 1.0},
    {"name": "Work Experience Placements",
     "description": "Facilitates short-term, structured work experience placements with local employers, enabling individuals to gain practical skills, build a work history, and boost confidence.",
     "type": "employment_support", "remote_chance": 0.1, "in_person_chance": 1.0},
    {"name": "Self-Employment Guidance",
     "description": "Comprehensive advice and support for unemployed individuals considering starting their own business, covering business planning, legal structures, marketing, and financial aspects.",
     "type": "business_support", "remote_chance": 0.8, "in_person_chance": 1.0},
    {"name": "Basic Skills Refresher (Literacy/Numeracy)",
     "description": "Tailored support and small group sessions to improve fundamental literacy and numeracy skills, essential for understanding job applications, workplace instructions, and daily tasks.",
     "type": "education", "remote_chance": 0.6, "in_person_chance": 1.0},
    {"name": "Confidence Building Workshops",
     "description": "Interactive workshops designed to boost self-esteem, improve public speaking, and enhance assertiveness, crucial for successful job applications and interviews.",
     "type": "personal_development", "remote_chance": 0.7, "in_person_chance": 1.0},
    {"name": "Access to Work Scheme Advice",
     "description": "Specialist guidance and support for disabled job seekers and those with health conditions to understand and apply for the 'Access to Work' scheme, which provides grants for workplace adaptations and support.",
     "type": "information_advice", "remote_chance": 0.9, "in_person_chance": 1.0},
    {"name": "Sector-Specific Training",
     "description": "Vocational training courses aligned with in-demand sectors (e.g., Health & Social Care, Warehousing, Customer Service), leading to recognised qualifications and improved employability.",
     "type": "vocational_training", "remote_chance": 0.4, "in_person_chance": 1.0},
    {"name": "Financial Inclusion Advice",
     "description": "Confidential advice and support with budgeting, debt management, and understanding benefit entitlements to alleviate financial stress and ensure stability during unemployment and transition into work.",
     "type": "financial_advice", "remote_chance": 0.9, "in_person_chance": 1.0},
    {"name": "Volunteer Opportunities Matching",
     "description": "Connects unemployed individuals with suitable volunteering roles to gain valuable experience, develop new skills, expand professional networks, and enhance well-being.",
     "type": "employment_support", "remote_chance": 0.5, "in_person_chance": 1.0},
    {"name": "Mock Interview Sessions with Feedback",
     "description": "Realistic interview practice sessions with experienced career coaches, followed by constructive, personalised feedback to help refine interview techniques and build confidence.",
     "type": "training", "remote_chance": 0.7, "in_person_chance": 1.0},
    {"name": "Online Job Application Support",
     "description": "Dedicated assistance with navigating online job portals, completing complex application forms, tailoring CVs and cover letters for online submissions, and managing job alerts.",
     "type": "information_advice", "remote_chance": 0.8, "in_person_chance": 1.0},
    {"name": "Dress for Success Programme",
     "description": "Provides professional clothing for interviews and the first few weeks of employment, along with styling advice, to boost confidence and make a strong first impression. Items are gently used and donated.",
     "type": "material_aid", "remote_chance": 0.0, "in_person_chance": 1.0},  # Must be in person
    {"name": "Networking Skills Training",
     "description": "Workshops on how to effectively network, build professional connections, utilise LinkedIn, and leverage contacts for hidden job opportunities and career advancement.",
     "type": "training", "remote_chance": 0.6, "in_person_chance": 1.0},
    {"name": "Job Fairs and Recruitment Events",
     "description": "Regular job fairs and recruitment events providing direct access to local employers, job vacancies, and networking opportunities.",
     "type": "event", "remote_chance": 0.0, "in_person_chance": 1.0},  # Must be in person
    {"name": "Support for Parents Seeking Work",
     "description": "Specialised advice and resources for parents balancing job search with childcare responsibilities, including information on flexible work options, childcare support schemes, and return-to-work programmes.",
     "type": "employment_support", "remote_chance": 0.8, "in_person_chance": 1.0},
    {"name": "Addiction Recovery Employment Support",
     "description": "Integrated support for individuals in addiction recovery, focusing on gaining stability, developing life skills, and re-entering the workforce through tailored employment advice and pathways.",
     "type": "rehabilitation", "remote_chance": 0.7, "in_person_chance": 1.0},
    {"name": "Disclosure and Barring Service (DBS) Guidance",
     "description": "Assistance with understanding Disclosure and Barring Service (DBS) checks, including how to obtain them and how to effectively address previous convictions during the job application and interview process.",
     "type": "information_advice", "remote_chance": 0.8, "in_person_chance": 1.0},
    {"name": "English Language Classes for Employment",
     "description": "ESOL (English for Speakers of Other Languages) classes specifically designed to improve vocabulary and communication skills relevant to the UK workplace, including interview practice and professional communication.",
     "type": "education", "remote_chance": 0.4, "in_person_chance": 1.0},
    {"name": "IT Access and Support Hub",
     "description": "Provides free, accessible public access to computers, internet, and printing facilities for all job search activities, with trained staff available to offer basic IT support and guidance.",
     "type": "facility", "remote_chance": 0.0, "in_person_chance": 1.0},  # Must be in person
    {"name": "Travel to Work Support (Funding/Advice)",
     "description": "Advice and potential financial support for travel costs associated with job interviews, training, or initial commute to a new job.",
     "type": "financial_aid", "remote_chance": 0.9, "in_person_chance": 0.5},
    {"name": "Health & Safety in the Workplace Training",
     "description": "Essential training covering basic health and safety regulations and practices relevant to various work environments.",
     "type": "training", "remote_chance": 0.5, "in_person_chance": 1.0},
    {"name": "Customer Service Skills Course",
     "description": "Develops key customer service skills, including communication, problem-solving, and handling difficult situations, applicable to many frontline roles.",
     "type": "vocational_training", "remote_chance": 0.7, "in_person_chance": 1.0},
    {"name": "Basic Food Hygiene Certificate",
     "description": "Accredited course providing the essential food hygiene knowledge required for roles in catering, hospitality, and food retail.",
     "type": "vocational_training", "remote_chance": 0.4, "in_person_chance": 1.0},
    {"name": "Driving Licence Support Programme",
     "description": "Assistance and funding advice for obtaining a driving licence, which can significantly expand employment opportunities.",
     "type": "financial_aid", "remote_chance": 0.8, "in_person_chance": 0.3},
    {"name": "Emergency Food Parcel Distribution",
     "description": "Provision of emergency food parcels to individuals and families experiencing food poverty. Referral usually required.",
     "type": "material_aid", "remote_chance": 0.0, "in_person_chance": 1.0},
    {"name": "Support for Long-Term Health Conditions (Employment Focus)",
     "description": "Peer support groups, workshops, and information on managing long-term health conditions to improve overall well-being and readiness for work, including workplace adjustments.",
     "type": "health", "remote_chance": 0.7, "in_person_chance": 1.0},
    {"name": "Childcare Information & Funding Advice",
     "description": "Guidance on available childcare options, free childcare entitlements (e.g., 15/30 hours), and financial support for childcare costs while seeking or in employment.",
     "type": "information_advice", "remote_chance": 0.9, "in_person_chance": 1.0},
    {"name": "Children's Activities during Job Search Workshops",
     "description": "Supervised activities for children (ages 3-11) provided on-site, enabling parents to attend employment support workshops or interviews.",
     "type": "child_care", "remote_chance": 0.0, "in_person_chance": 1.0},
    {"name": "Housing and Homelessness Advice",
     "description": "Advice and support for individuals experiencing housing issues or homelessness, which can be a significant barrier to employment.",
     "type": "housing", "remote_chance": 0.8, "in_person_chance": 1.0},
    {"name": "Benefit Claims and Appeals Support",
     "description": "Assistance with understanding and applying for various welfare benefits, as well as support with appeals processes.",
     "type": "financial_advice", "remote_chance": 0.9, "in_person_chance": 1.0},
    {"name": "IT Skills for Older Job Seekers",
     "description": "Tailored, slower-paced IT training specifically for older individuals seeking to re-enter the workforce, covering online applications, email, and digital communication.",
     "type": "training", "remote_chance": 0.6, "in_person_chance": 1.0}
]

# --- 4. Mapping Organizations to Locations and Service Areas ---
# This dictionary helps assign locations based on the organization and service area.
# Each key represents an organization, and its value is another dictionary
# mapping service areas (Huddersfield/Wakefield) to a list of eligible location IDs.
org_location_map = {
    "kirklees_council": {
        "Huddersfield": [
            locations["hudd_lib"]["id"], locations["hudd_jcp"]["id"],
            locations["hudd_community_hub_central"]["id"], locations["st_pauls_church_hudd"]["id"],
            locations["dewsbury_lib"]["id"], locations["batley_community_centre"]["id"],
            locations["mirfield_methodist_hall"]["id"], locations["holmfirth_civic_hall"]["id"],
            locations["st_pauls_dewsbury_church"]["id"], locations["batley_jcp_outreach"]["id"]
        ],
        "Wakefield": []
    },
    "wakefield_council": {
        "Wakefield": [
            locations["wake_one"]["id"], locations["wake_jcp"]["id"],
            locations["eastmoor_community_centre"]["id"], locations["castleford_lib"]["id"],
            locations["pontefract_lib"]["id"], locations["ossett_town_hall"]["id"],
            locations["ackworth_village_hall"]["id"], locations["featherstone_community_centre"]["id"]
        ],
        "Huddersfield": []
    },
    "jp_huddersfield": {
        "Huddersfield": [locations["hudd_jcp"]["id"], locations["hudd_lib"]["id"],
                         locations["batley_jcp_outreach"]["id"]],
        "Wakefield": []
    },
    "jp_wakefield": {
        "Wakefield": [locations["wake_jcp"]["id"], locations["wake_one"]["id"], locations["castleford_lib"]["id"],
                      locations["pontefract_lib"]["id"]],
        "Huddersfield": []
    },
    "kirklees_college": {
        "Huddersfield": [locations["kirklees_college_hudd"]["id"], locations["hudd_lib"]["id"],
                         locations["dewsbury_lib"]["id"], locations["batley_community_centre"]["id"]],
        "Wakefield": []
    },
    "wakefield_college": {
        "Wakefield": [locations["wakefield_college_city"]["id"], locations["wake_one"]["id"],
                      locations["castleford_lib"]["id"], locations["pontefract_lib"]["id"],
                      locations["featherstone_community_centre"]["id"]],
        "Huddersfield": []
    },
    "citizens_advice_kirklees": {
        "Huddersfield": [locations["hudd_citizens_advice"]["id"], locations["hudd_lib"]["id"],
                         locations["dewsbury_lib"]["id"], locations["batley_community_centre"]["id"],
                         locations["mirfield_methodist_hall"]["id"]],
        "Wakefield": []
    },
    "citizens_advice_wakefield": {
        "Wakefield": [locations["wake_citizens_advice"]["id"], locations["wake_one"]["id"],
                      locations["castleford_lib"]["id"], locations["pontefract_lib"]["id"],
                      locations["ossett_town_hall"]["id"]],
        "Huddersfield": []
    },
    "the_welcome_centre_hudd": {
        "Huddersfield": [locations["hudd_welcome_centre_loc"]["id"], locations["st_pauls_church_hudd"]["id"],
                         locations["hudd_community_hub_central"]["id"]],
        "Wakefield": []
    },
    "wakefield_foodbank": {
        "Wakefield": [locations["wakefield_foodbank_main"]["id"], locations["eastmoor_community_centre"]["id"],
                      locations["wakefield_cathedral_loc"]["id"], locations["wakefield_city_church"]["id"],
                      locations["ackworth_village_hall"]["id"]],
        "Huddersfield": []
    },
    "kirklees_health_alliance": {
        "Huddersfield": [locations["gp_hudd_central"]["id"], locations["hudd_lib"]["id"],
                         locations["hudd_community_hub_central"]["id"], locations["dewsbury_lib"]["id"]],
        "Wakefield": []
    },
    "wakefield_wellbeing_hub": {
        "Wakefield": [locations["gp_wake_north"]["id"], locations["wake_one"]["id"],
                      locations["eastmoor_community_centre"]["id"], locations["ossett_town_hall"]["id"]],
        "Huddersfield": []
    },
    "kirklees_childrens_centre": {
        "Huddersfield": [locations["hudd_lib"]["id"], locations["hudd_community_hub_central"]["id"],
                         locations["st_pauls_church_hudd"]["id"], locations["dewsbury_lib"]["id"],
                         locations["batley_community_centre"]["id"]],
        "Wakefield": []
    },
    "wakefield_family_support": {
        "Wakefield": [locations["wake_one"]["id"], locations["eastmoor_community_centre"]["id"],
                      locations["castleford_lib"]["id"], locations["pontefract_lib"]["id"],
                      locations["wakefield_city_church"]["id"]],
        "Huddersfield": []
    },
    "community_action_hudd": {
        "Huddersfield": [locations["hudd_community_hub_central"]["id"], locations["hudd_lib"]["id"],
                         locations["kirkheaton_scout_hq"]["id"], locations["mirfield_methodist_hall"]["id"]],
        "Wakefield": []
    },
    "wakefield_community_link": {
        "Wakefield": [locations["eastmoor_community_centre"]["id"], locations["wakefield_cathedral_loc"]["id"],
                      locations["sandal_scout_hq"]["id"], locations["featherstone_community_centre"]["id"]],
        "Huddersfield": []
    },
    "scouts_kirklees": {
        "Huddersfield": [locations["kirkheaton_scout_hq"]["id"], locations["hudd_community_hub_central"]["id"]],
        "Wakefield": []
    },
    "scouts_wakefield": {
        "Wakefield": [locations["sandal_scout_hq"]["id"], locations["eastmoor_community_centre"]["id"],
                      locations["ackworth_village_hall"]["id"]],
        "Huddersfield": []
    },
    "church_halls_kirklees": {
        "Huddersfield": [locations["st_pauls_church_hudd"]["id"], locations["st_pauls_dewsbury_church"]["id"],
                         locations["mirfield_methodist_hall"]["id"]],
        "Wakefield": []
    },
    "church_halls_wakefield": {
        "Wakefield": [locations["wakefield_cathedral_loc"]["id"], locations["wakefield_city_church"]["id"],
                      locations["eastmoor_community_centre"]["id"], locations["ackworth_village_hall"]["id"]],
        "Huddersfield": []
    }
}


# --- Utility for generating schedules ---
def generate_random_schedule(is_event=False):
    schedule_type = random.choice(["regular", "event_specific"])

    if is_event or schedule_type == "event_specific":
        # Events might have very specific, one-off or short durations
        start_hour = random.randint(9, 17)
        duration_hours = random.randint(1, 5)  # Events can be longer
        opens_at = f"{start_hour:02d}:00"
        closes_at = f"{(start_hour + duration_hours):02d}:00"

        # Ensure the date is in the near future from current date (June 28, 2025)
        current_date = datetime(2025, 6, 28)
        event_date = (current_date + timedelta(days=random.randint(1, 90))).strftime("%Y-%m-%d")  # Next 3 months

        return {
            "opens_at": opens_at,
            "closes_at": closes_at,
            "valid_from": event_date,
            "valid_to": event_date,
            "description": "One-off event or specific session, check website for next date."
        }
    else:
        # Regular weekly schedule
        start_hour = random.randint(9, 10)  # Morning start
        end_hour = random.randint(16, 17)  # Afternoon/early evening end

        opens_at = f"{start_hour:02d}:00"
        closes_at = f"{end_hour:02d}:00"

        num_days = random.randint(2, 5)  # 2-5 days a week
        weekdays = random.sample(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], num_days)
        weekdays.sort(
            key=lambda d: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(d))

        return {
            "opens_at": opens_at,
            "closes_at": closes_at,
            "valid_for_weekdays": weekdays,
            "description": "Regular weekly operating hours."
        }


# --- Generate Service Offers ---
service_offers = []
num_offers_to_generate = 200  # Significantly increased to ensure broad coverage

for i in range(num_offers_to_generate):
    service_id = generate_uuid()

    service_area_name = random.choice(["Huddersfield", "Wakefield"])

    eligible_org_keys = [
        k for k, v in org_location_map.items()
        if service_area_name in v and len(v[service_area_name]) > 0
    ]

    if not eligible_org_keys:
        # print(f"Warning: No eligible organizations for {service_area_name}, skipping service {i}") # Debugging
        continue

    org_key = random.choice(eligible_org_keys)
    org_data = organizations[org_key]

    location_id = random.choice(org_location_map[org_key][service_area_name])
    location_data = next((loc for loc in locations.values() if loc["id"] == location_id))

    service_type_info = random.choice(service_types)

    remote_status = random.random() < service_type_info["remote_chance"]
    in_person_status = random.random() < service_type_info["in_person_chance"]

    if not service_type_info["type"] == "event" and not (remote_status or in_person_status):
        if service_type_info["in_person_chance"] > 0:
            in_person_status = True
        elif service_type_info["remote_chance"] > 0:
            remote_status = True

    schedule = generate_random_schedule(is_event=(service_type_info["type"] == "event"))

    offer = {
        "id": generate_uuid(),
        "service_id": service_id,
        "location_id": location_id,
        "organization_id": org_data["id"],
        "name": f"{service_type_info['name']} - {service_area_name} ({location_data['name'].split('(')[0].strip()})",
        # Added location to name for variety
        "description": f"{service_type_info['description']} This service is provided by {org_data['name']} for residents in {service_area_name}.",
        "url": org_data["url"],
        "status": "active",
        "type": service_type_info["type"],
        "in_person": in_person_status,
        "remote": remote_status,
        "interpretation_services": random.choice([True, False, False, False]),
        "phone_support": random.choice([True, True, False, False]),
        "online_support": random.choice([True, True, False, False]),
        "cost_options": [
            {
                "amount": 0.00,
                "amount_description": "Free for eligible individuals",
                "option": "No Cost"
            }
        ],
        "eligibility": f"Unemployed individuals residing in {service_area_name}.",
        "service_areas": [
            {
                "name": service_area_name
            }
        ],
        "service_schedules": [schedule],
        "organisation": org_data,
        "location": location_data
    }
    service_offers.append(offer)

# Output the JSON
print(json.dumps(service_offers, indent=2))