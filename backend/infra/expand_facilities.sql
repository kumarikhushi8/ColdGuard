-- ColdGuard National Expansion Migration
-- 9 states × 5 facilities = 45 new facilities
-- Run after existing init.sql is applied

-- ─── Punjab (5 facilities) ────────────────────────────────────────────────────
INSERT INTO facilities (id, name, location, owner_name, owner_phone, capacity_mt) VALUES
    ('a2000001-0000-0000-0000-000000000001', 'Amritsar ColdStore Prime',   'Amritsar, Punjab',     'Gurpreet Singh',    '+919815001001', 800),
    ('a2000001-0000-0000-0000-000000000002', 'Ludhiana Agri Hub',          'Ludhiana, Punjab',     'Harjinder Kaur',    '+919815001002', 1200),
    ('a2000001-0000-0000-0000-000000000003', 'Jalandhar Potato Store',     'Jalandhar, Punjab',    'Balwinder Singh',   '+919815001003', 600),
    ('a2000001-0000-0000-0000-000000000004', 'Patiala Farm Cold',          'Patiala, Punjab',      'Kulwant Kaur',      '+919815001004', 450),
    ('a2000001-0000-0000-0000-000000000005', 'Bhatinda Onion Hub',         'Bhatinda, Punjab',     'Sukhdev Singh',     '+919815001005', 750)
ON CONFLICT DO NOTHING;

-- ─── Uttar Pradesh (5 facilities) ─────────────────────────────────────────────
INSERT INTO facilities (id, name, location, owner_name, owner_phone, capacity_mt) VALUES
    ('a2000002-0000-0000-0000-000000000001', 'Agra Potato Cold Hub',       'Agra, Uttar Pradesh',          'Ramesh Sharma',     '+919412002001', 900),
    ('a2000002-0000-0000-0000-000000000002', 'Lucknow Mango Store',        'Lucknow, Uttar Pradesh',       'Priya Verma',       '+919412002002', 400),
    ('a2000002-0000-0000-0000-000000000003', 'Allahabad Guava Hub',        'Prayagraj, Uttar Pradesh',     'Suresh Mishra',     '+919412002003', 300),
    ('a2000002-0000-0000-0000-000000000004', 'Varanasi Agri Cold',         'Varanasi, Uttar Pradesh',      'Anita Gupta',       '+919412002004', 500),
    ('a2000002-0000-0000-0000-000000000005', 'Mathura Potato Store',       'Mathura, Uttar Pradesh',       'Vinod Yadav',       '+919412002005', 700)
ON CONFLICT DO NOTHING;

-- ─── Karnataka (5 facilities) ─────────────────────────────────────────────────
INSERT INTO facilities (id, name, location, owner_name, owner_phone, capacity_mt) VALUES
    ('a2000003-0000-0000-0000-000000000001', 'Hubli Grapes ColdStore',     'Hubli, Karnataka',     'Prakash Desai',     '+919986003001', 600),
    ('a2000003-0000-0000-0000-000000000002', 'Bangalore Tomato Hub',       'Bangalore, Karnataka', 'Kavitha Reddy',     '+919986003002', 350),
    ('a2000003-0000-0000-0000-000000000003', 'Belgaum Pomegranate Store',  'Belagavi, Karnataka',  'Suresh Patil',      '+919986003003', 450),
    ('a2000003-0000-0000-0000-000000000004', 'Shimoga Fruits Cold',        'Shivamogga, Karnataka','Ranjitha Gowda',    '+919986003004', 280),
    ('a2000003-0000-0000-0000-000000000005', 'Mysore Agri Hub',            'Mysore, Karnataka',    'Nagaraj Kumar',     '+919986003005', 500)
ON CONFLICT DO NOTHING;

-- ─── Gujarat (5 facilities) ───────────────────────────────────────────────────
INSERT INTO facilities (id, name, location, owner_name, owner_phone, capacity_mt) VALUES
    ('a2000004-0000-0000-0000-000000000001', 'Surat Banana Hub',           'Surat, Gujarat',       'Nilesh Patel',      '+919898004001', 700),
    ('a2000004-0000-0000-0000-000000000002', 'Rajkot Potato ColdStore',    'Rajkot, Gujarat',      'Bhavna Shah',       '+919898004002', 850),
    ('a2000004-0000-0000-0000-000000000003', 'Junagadh Mango Store',       'Junagadh, Gujarat',    'Haresh Mehta',      '+919898004003', 400),
    ('a2000004-0000-0000-0000-000000000004', 'Anand Agri Cold Hub',        'Anand, Gujarat',       'Varsha Patel',      '+919898004004', 600),
    ('a2000004-0000-0000-0000-000000000005', 'Bhavnagar Fruits Store',     'Bhavnagar, Gujarat',   'Mahesh Joshi',      '+919898004005', 320)
ON CONFLICT DO NOTHING;

-- ─── Himachal Pradesh (5 facilities) ──────────────────────────────────────────
INSERT INTO facilities (id, name, location, owner_name, owner_phone, capacity_mt) VALUES
    ('a2000005-0000-0000-0000-000000000001', 'Shimla Apple ColdStore',     'Shimla, Himachal Pradesh',     'Rajender Thakur',   '+919816005001', 500),
    ('a2000005-0000-0000-0000-000000000002', 'Manali Fruits Hub',          'Manali, Himachal Pradesh',     'Sunita Rana',       '+919816005002', 200),
    ('a2000005-0000-0000-0000-000000000003', 'Kullu Apple Store',          'Kullu, Himachal Pradesh',      'Mohan Verma',       '+919816005003', 350),
    ('a2000005-0000-0000-0000-000000000004', 'Mandi Pear Hub',             'Mandi, Himachal Pradesh',      'Kamla Devi',        '+919816005004', 180),
    ('a2000005-0000-0000-0000-000000000005', 'Solan Cherry Store',         'Solan, Himachal Pradesh',      'Deepak Sharma',     '+919816005005', 150)
ON CONFLICT DO NOTHING;

-- ─── Rajasthan (5 facilities) ─────────────────────────────────────────────────
INSERT INTO facilities (id, name, location, owner_name, owner_phone, capacity_mt) VALUES
    ('a2000006-0000-0000-0000-000000000001', 'Jaipur Onion ColdStore',     'Jaipur, Rajasthan',    'Ramdev Sharma',     '+919829006001', 900),
    ('a2000006-0000-0000-0000-000000000002', 'Jodhpur Garlic Hub',         'Jodhpur, Rajasthan',   'Shanti Devi',       '+919829006002', 550),
    ('a2000006-0000-0000-0000-000000000003', 'Alwar Chilli Store',         'Alwar, Rajasthan',     'Bhagwan Das',       '+919829006003', 400),
    ('a2000006-0000-0000-0000-000000000004', 'Kota Agri Cold Hub',         'Kota, Rajasthan',      'Preeti Gupta',      '+919829006004', 650),
    ('a2000006-0000-0000-0000-000000000005', 'Bikaner Onion Store',        'Bikaner, Rajasthan',   'Suresh Pareek',     '+919829006005', 480)
ON CONFLICT DO NOTHING;

-- ─── West Bengal (5 facilities) ───────────────────────────────────────────────
INSERT INTO facilities (id, name, location, owner_name, owner_phone, capacity_mt) VALUES
    ('a2000007-0000-0000-0000-000000000001', 'Kolkata Potato Hub',         'Kolkata, West Bengal',         'Subhas Chatterjee', '+919831007001', 1000),
    ('a2000007-0000-0000-0000-000000000002', 'Siliguri Mango Store',       'Siliguri, West Bengal',        'Mitali Das',        '+919831007002', 350),
    ('a2000007-0000-0000-0000-000000000003', 'Murshidabad Lychee Hub',     'Murshidabad, West Bengal',     'Rahim Mondal',      '+919831007003', 200),
    ('a2000007-0000-0000-0000-000000000004', 'Hooghly Agri Cold',          'Hooghly, West Bengal',         'Suparna Roy',       '+919831007004', 450),
    ('a2000007-0000-0000-0000-000000000005', 'Burdwan Potato Store',       'Burdwan, West Bengal',         'Pranab Ghosh',      '+919831007005', 700)
ON CONFLICT DO NOTHING;

-- ─── Tamil Nadu (5 facilities) ────────────────────────────────────────────────
INSERT INTO facilities (id, name, location, owner_name, owner_phone, capacity_mt) VALUES
    ('a2000008-0000-0000-0000-000000000001', 'Coimbatore Banana Hub',      'Coimbatore, Tamil Nadu',       'Murugan Pillai',    '+919842008001', 600),
    ('a2000008-0000-0000-0000-000000000002', 'Salem Tomato ColdStore',     'Salem, Tamil Nadu',            'Lakshmi Devi',      '+919842008002', 400),
    ('a2000008-0000-0000-0000-000000000003', 'Madurai Mango Store',        'Madurai, Tamil Nadu',          'Arumugam Raja',     '+919842008003', 500),
    ('a2000008-0000-0000-0000-000000000004', 'Tiruchirappalli Agri Hub',   'Tiruchirappalli, Tamil Nadu',  'Kavitha Sundaram',  '+919842008004', 350),
    ('a2000008-0000-0000-0000-000000000005', 'Erode Banana Hub',           'Erode, Tamil Nadu',            'Selvam Gopal',      '+919842008005', 280)
ON CONFLICT DO NOTHING;

-- ─── Bihar (5 facilities) ─────────────────────────────────────────────────────
INSERT INTO facilities (id, name, location, owner_name, owner_phone, capacity_mt) VALUES
    ('a2000009-0000-0000-0000-000000000001', 'Patna Mango ColdStore',      'Patna, Bihar',         'Ramchandra Prasad',  '+919934009001', 450),
    ('a2000009-0000-0000-0000-000000000002', 'Muzaffarpur Lychee Hub',     'Muzaffarpur, Bihar',   'Sarita Devi',        '+919934009002', 250),
    ('a2000009-0000-0000-0000-000000000003', 'Gaya Agri Cold',             'Gaya, Bihar',          'Rajesh Kumar',       '+919934009003', 300),
    ('a2000009-0000-0000-0000-000000000004', 'Bhagalpur Fruits Store',     'Bhagalpur, Bihar',     'Manju Kumari',       '+919934009004', 200),
    ('a2000009-0000-0000-0000-000000000005', 'Darbhanga Potato Hub',       'Darbhanga, Bihar',     'Santosh Singh',      '+919934009005', 350)
ON CONFLICT DO NOTHING;

-- ─── Sensors: 2 per facility for all new facilities ───────────────────────────
-- Punjab sensors
INSERT INTO sensors (facility_id, sensor_code, type, location) VALUES
    ('a2000001-0000-0000-0000-000000000001', 'PB-AMR-001', 'combined', 'Main chamber'),
    ('a2000001-0000-0000-0000-000000000001', 'PB-AMR-002', 'combined', 'Loading dock'),
    ('a2000001-0000-0000-0000-000000000002', 'PB-LDH-001', 'combined', 'Zone A'),
    ('a2000001-0000-0000-0000-000000000002', 'PB-LDH-002', 'combined', 'Zone B'),
    ('a2000001-0000-0000-0000-000000000003', 'PB-JLD-001', 'combined', 'Main chamber'),
    ('a2000001-0000-0000-0000-000000000003', 'PB-JLD-002', 'combined', 'Entry zone'),
    ('a2000001-0000-0000-0000-000000000004', 'PB-PAT-001', 'combined', 'Main chamber'),
    ('a2000001-0000-0000-0000-000000000004', 'PB-PAT-002', 'combined', 'Cold room 2'),
    ('a2000001-0000-0000-0000-000000000005', 'PB-BTD-001', 'combined', 'Primary zone'),
    ('a2000001-0000-0000-0000-000000000005', 'PB-BTD-002', 'combined', 'Secondary zone')
ON CONFLICT (sensor_code) DO NOTHING;

-- UP sensors
INSERT INTO sensors (facility_id, sensor_code, type, location) VALUES
    ('a2000002-0000-0000-0000-000000000001', 'UP-AGR-001', 'combined', 'Main chamber'),
    ('a2000002-0000-0000-0000-000000000001', 'UP-AGR-002', 'combined', 'Loading dock'),
    ('a2000002-0000-0000-0000-000000000002', 'UP-LKO-001', 'combined', 'Cold room 1'),
    ('a2000002-0000-0000-0000-000000000002', 'UP-LKO-002', 'combined', 'Cold room 2'),
    ('a2000002-0000-0000-0000-000000000003', 'UP-ALD-001', 'combined', 'Main chamber'),
    ('a2000002-0000-0000-0000-000000000003', 'UP-ALD-002', 'combined', 'Entry zone'),
    ('a2000002-0000-0000-0000-000000000004', 'UP-VNS-001', 'combined', 'Main chamber'),
    ('a2000002-0000-0000-0000-000000000004', 'UP-VNS-002', 'combined', 'Cold room 2'),
    ('a2000002-0000-0000-0000-000000000005', 'UP-MTH-001', 'combined', 'Zone A'),
    ('a2000002-0000-0000-0000-000000000005', 'UP-MTH-002', 'combined', 'Zone B')
ON CONFLICT (sensor_code) DO NOTHING;

-- Karnataka sensors
INSERT INTO sensors (facility_id, sensor_code, type, location) VALUES
    ('a2000003-0000-0000-0000-000000000001', 'KA-HBL-001', 'combined', 'Main chamber'),
    ('a2000003-0000-0000-0000-000000000001', 'KA-HBL-002', 'combined', 'Loading dock'),
    ('a2000003-0000-0000-0000-000000000002', 'KA-BLR-001', 'combined', 'Cold room 1'),
    ('a2000003-0000-0000-0000-000000000002', 'KA-BLR-002', 'combined', 'Cold room 2'),
    ('a2000003-0000-0000-0000-000000000003', 'KA-BLG-001', 'combined', 'Main chamber'),
    ('a2000003-0000-0000-0000-000000000003', 'KA-BLG-002', 'combined', 'Entry zone'),
    ('a2000003-0000-0000-0000-000000000004', 'KA-SMG-001', 'combined', 'Main chamber'),
    ('a2000003-0000-0000-0000-000000000004', 'KA-SMG-002', 'combined', 'Cold room 2'),
    ('a2000003-0000-0000-0000-000000000005', 'KA-MYS-001', 'combined', 'Zone A'),
    ('a2000003-0000-0000-0000-000000000005', 'KA-MYS-002', 'combined', 'Zone B')
ON CONFLICT (sensor_code) DO NOTHING;

-- Gujarat sensors
INSERT INTO sensors (facility_id, sensor_code, type, location) VALUES
    ('a2000004-0000-0000-0000-000000000001', 'GJ-SRT-001', 'combined', 'Main chamber'),
    ('a2000004-0000-0000-0000-000000000001', 'GJ-SRT-002', 'combined', 'Loading dock'),
    ('a2000004-0000-0000-0000-000000000002', 'GJ-RJK-001', 'combined', 'Cold room 1'),
    ('a2000004-0000-0000-0000-000000000002', 'GJ-RJK-002', 'combined', 'Cold room 2'),
    ('a2000004-0000-0000-0000-000000000003', 'GJ-JNG-001', 'combined', 'Main chamber'),
    ('a2000004-0000-0000-0000-000000000003', 'GJ-JNG-002', 'combined', 'Entry zone'),
    ('a2000004-0000-0000-0000-000000000004', 'GJ-AND-001', 'combined', 'Main chamber'),
    ('a2000004-0000-0000-0000-000000000004', 'GJ-AND-002', 'combined', 'Cold room 2'),
    ('a2000004-0000-0000-0000-000000000005', 'GJ-BVN-001', 'combined', 'Zone A'),
    ('a2000004-0000-0000-0000-000000000005', 'GJ-BVN-002', 'combined', 'Zone B')
ON CONFLICT (sensor_code) DO NOTHING;

-- Himachal sensors
INSERT INTO sensors (facility_id, sensor_code, type, location) VALUES
    ('a2000005-0000-0000-0000-000000000001', 'HP-SML-001', 'combined', 'Main chamber'),
    ('a2000005-0000-0000-0000-000000000001', 'HP-SML-002', 'combined', 'Loading dock'),
    ('a2000005-0000-0000-0000-000000000002', 'HP-MNL-001', 'combined', 'Cold room 1'),
    ('a2000005-0000-0000-0000-000000000002', 'HP-MNL-002', 'combined', 'Cold room 2'),
    ('a2000005-0000-0000-0000-000000000003', 'HP-KLU-001', 'combined', 'Main chamber'),
    ('a2000005-0000-0000-0000-000000000003', 'HP-KLU-002', 'combined', 'Entry zone'),
    ('a2000005-0000-0000-0000-000000000004', 'HP-MND-001', 'combined', 'Main chamber'),
    ('a2000005-0000-0000-0000-000000000004', 'HP-MND-002', 'combined', 'Cold room 2'),
    ('a2000005-0000-0000-0000-000000000005', 'HP-SLN-001', 'combined', 'Zone A'),
    ('a2000005-0000-0000-0000-000000000005', 'HP-SLN-002', 'combined', 'Zone B')
ON CONFLICT (sensor_code) DO NOTHING;

-- Rajasthan sensors
INSERT INTO sensors (facility_id, sensor_code, type, location) VALUES
    ('a2000006-0000-0000-0000-000000000001', 'RJ-JAI-001', 'combined', 'Main chamber'),
    ('a2000006-0000-0000-0000-000000000001', 'RJ-JAI-002', 'combined', 'Loading dock'),
    ('a2000006-0000-0000-0000-000000000002', 'RJ-JDH-001', 'combined', 'Cold room 1'),
    ('a2000006-0000-0000-0000-000000000002', 'RJ-JDH-002', 'combined', 'Cold room 2'),
    ('a2000006-0000-0000-0000-000000000003', 'RJ-ALW-001', 'combined', 'Main chamber'),
    ('a2000006-0000-0000-0000-000000000003', 'RJ-ALW-002', 'combined', 'Entry zone'),
    ('a2000006-0000-0000-0000-000000000004', 'RJ-KOT-001', 'combined', 'Main chamber'),
    ('a2000006-0000-0000-0000-000000000004', 'RJ-KOT-002', 'combined', 'Cold room 2'),
    ('a2000006-0000-0000-0000-000000000005', 'RJ-BKN-001', 'combined', 'Zone A'),
    ('a2000006-0000-0000-0000-000000000005', 'RJ-BKN-002', 'combined', 'Zone B')
ON CONFLICT (sensor_code) DO NOTHING;

-- West Bengal sensors
INSERT INTO sensors (facility_id, sensor_code, type, location) VALUES
    ('a2000007-0000-0000-0000-000000000001', 'WB-KOL-001', 'combined', 'Main chamber'),
    ('a2000007-0000-0000-0000-000000000001', 'WB-KOL-002', 'combined', 'Loading dock'),
    ('a2000007-0000-0000-0000-000000000002', 'WB-SLG-001', 'combined', 'Cold room 1'),
    ('a2000007-0000-0000-0000-000000000002', 'WB-SLG-002', 'combined', 'Cold room 2'),
    ('a2000007-0000-0000-0000-000000000003', 'WB-MRD-001', 'combined', 'Main chamber'),
    ('a2000007-0000-0000-0000-000000000003', 'WB-MRD-002', 'combined', 'Entry zone'),
    ('a2000007-0000-0000-0000-000000000004', 'WB-HGL-001', 'combined', 'Main chamber'),
    ('a2000007-0000-0000-0000-000000000004', 'WB-HGL-002', 'combined', 'Cold room 2'),
    ('a2000007-0000-0000-0000-000000000005', 'WB-BRD-001', 'combined', 'Zone A'),
    ('a2000007-0000-0000-0000-000000000005', 'WB-BRD-002', 'combined', 'Zone B')
ON CONFLICT (sensor_code) DO NOTHING;

-- Tamil Nadu sensors
INSERT INTO sensors (facility_id, sensor_code, type, location) VALUES
    ('a2000008-0000-0000-0000-000000000001', 'TN-CBE-001', 'combined', 'Main chamber'),
    ('a2000008-0000-0000-0000-000000000001', 'TN-CBE-002', 'combined', 'Loading dock'),
    ('a2000008-0000-0000-0000-000000000002', 'TN-SLM-001', 'combined', 'Cold room 1'),
    ('a2000008-0000-0000-0000-000000000002', 'TN-SLM-002', 'combined', 'Cold room 2'),
    ('a2000008-0000-0000-0000-000000000003', 'TN-MDU-001', 'combined', 'Main chamber'),
    ('a2000008-0000-0000-0000-000000000003', 'TN-MDU-002', 'combined', 'Entry zone'),
    ('a2000008-0000-0000-0000-000000000004', 'TN-TRY-001', 'combined', 'Main chamber'),
    ('a2000008-0000-0000-0000-000000000004', 'TN-TRY-002', 'combined', 'Cold room 2'),
    ('a2000008-0000-0000-0000-000000000005', 'TN-ERD-001', 'combined', 'Zone A'),
    ('a2000008-0000-0000-0000-000000000005', 'TN-ERD-002', 'combined', 'Zone B')
ON CONFLICT (sensor_code) DO NOTHING;

-- Bihar sensors
INSERT INTO sensors (facility_id, sensor_code, type, location) VALUES
    ('a2000009-0000-0000-0000-000000000001', 'BR-PAT-001', 'combined', 'Main chamber'),
    ('a2000009-0000-0000-0000-000000000001', 'BR-PAT-002', 'combined', 'Loading dock'),
    ('a2000009-0000-0000-0000-000000000002', 'BR-MZF-001', 'combined', 'Cold room 1'),
    ('a2000009-0000-0000-0000-000000000002', 'BR-MZF-002', 'combined', 'Cold room 2'),
    ('a2000009-0000-0000-0000-000000000003', 'BR-GAY-001', 'combined', 'Main chamber'),
    ('a2000009-0000-0000-0000-000000000003', 'BR-GAY-002', 'combined', 'Entry zone'),
    ('a2000009-0000-0000-0000-000000000004', 'BR-BGL-001', 'combined', 'Main chamber'),
    ('a2000009-0000-0000-0000-000000000004', 'BR-BGL-002', 'combined', 'Cold room 2'),
    ('a2000009-0000-0000-0000-000000000005', 'BR-DBG-001', 'combined', 'Zone A'),
    ('a2000009-0000-0000-0000-000000000005', 'BR-DBG-002', 'combined', 'Zone B')
ON CONFLICT (sensor_code) DO NOTHING;
