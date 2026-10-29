import csv
import json
import os

os.makedirs("data", exist_ok=True)

# Curated rich biomedical dataset: ~140 records covering major therapeutic areas
records = [
    # Metformin
    {"drug": "Metformin", "drug_class": "Biguanide", "disease": "Type 2 Diabetes Mellitus", "disease_category": "Endocrine & Metabolic", "symptom": "Hyperglycemia", "side_effect": "Gastrointestinal Upset", "mechanism": "Inhibits hepatic gluconeogenesis via AMP-activated protein kinase (AMPK) activation and increases peripheral insulin sensitivity.", "citation": "FDA-NDA-020357; PMID:31548545"},
    {"drug": "Metformin", "drug_class": "Biguanide", "disease": "Polycystic Ovary Syndrome", "disease_category": "Endocrine & Reproductive", "symptom": "Insulin Resistance", "side_effect": "Lactic Acidosis", "mechanism": "Ameliorates hyperinsulinemia, leading to decreased ovarian androgen synthesis.", "citation": "PMID:28938445"},
    {"drug": "Metformin", "drug_class": "Biguanide", "disease": "Type 2 Diabetes Mellitus", "disease_category": "Endocrine & Metabolic", "symptom": "Polyuria", "side_effect": "Vitamin B12 Deficiency", "mechanism": "Interferes with calcium-dependent ileal absorption of the vitamin B12-intrinsic factor complex.", "citation": "PMID:26900641"},
    {"drug": "Metformin", "drug_class": "Biguanide", "disease": "Metabolic Syndrome", "disease_category": "Endocrine & Metabolic", "symptom": "Acanthosis Nigricans", "side_effect": "Metallic Taste", "mechanism": "Enhances insulin-mediated glucose disposal into skeletal muscle.", "citation": "PMID:17924864"},

    # Semaglutide
    {"drug": "Semaglutide", "drug_class": "GLP-1 Receptor Agonist", "disease": "Type 2 Diabetes Mellitus", "disease_category": "Endocrine & Metabolic", "symptom": "Hyperglycemia", "side_effect": "Nausea", "mechanism": "Selectively binds and activates GLP-1 receptors, stimulating glucose-dependent insulin secretion and suppressing glucagon.", "citation": "FDA-BLA-125697; PMID:34125345"},
    {"drug": "Semaglutide", "drug_class": "GLP-1 Receptor Agonist", "disease": "Obesity", "disease_category": "Metabolic", "symptom": "Excess Adiposity", "side_effect": "Vomiting", "mechanism": "Delays gastric emptying and acts on hypothalamic feeding centers to enhance satiety.", "citation": "PMID:33567185"},
    {"drug": "Semaglutide", "drug_class": "GLP-1 Receptor Agonist", "disease": "Obesity", "disease_category": "Metabolic", "symptom": "Hyperphagia", "side_effect": "Pancreatitis Risk", "mechanism": "GLP-1 pathway stimulation promotes postprandial fullness and reduced caloric intake.", "citation": "FDA-BLA-125697"},
    {"drug": "Semaglutide", "drug_class": "GLP-1 Receptor Agonist", "disease": "Cardiovascular Disease in Diabetics", "disease_category": "Cardiovascular", "symptom": "Arterial Stiffness", "side_effect": "Constipation", "mechanism": "Reduces systemic vascular inflammation and major adverse cardiovascular events (MACE).", "citation": "PMID:38060356"},

    # Tirzepatide
    {"drug": "Tirzepatide", "drug_class": "Dual GIP and GLP-1 Receptor Agonist", "disease": "Type 2 Diabetes Mellitus", "disease_category": "Endocrine & Metabolic", "symptom": "Hyperglycemia", "side_effect": "Diarrhea", "mechanism": "Dual agonism of GIP and GLP-1 receptors synergistically enhances beta-cell insulin secretion and reduces glucagon levels.", "citation": "FDA-NDA-215866; PMID:34170797"},
    {"drug": "Tirzepatide", "drug_class": "Dual GIP and GLP-1 Receptor Agonist", "disease": "Obesity", "disease_category": "Metabolic", "symptom": "Excess Adiposity", "side_effect": "Decreased Appetite", "mechanism": "Modulates central hypothalamic circuits governing food intake and body weight set-point.", "citation": "PMID:35658024"},

    # Empagliflozin
    {"drug": "Empagliflozin", "drug_class": "SGLT2 Inhibitor", "disease": "Type 2 Diabetes Mellitus", "disease_category": "Endocrine & Metabolic", "symptom": "Hyperglycemia", "side_effect": "Genital Mycotic Infections", "mechanism": "Inhibits sodium-glucose cotransporter-2 (SGLT2) in proximal renal tubules, inducing urinary excretion of glucose.", "citation": "FDA-NDA-204629; PMID:26378978"},
    {"drug": "Empagliflozin", "drug_class": "SGLT2 Inhibitor", "disease": "Heart Failure with Reduced Ejection Fraction", "disease_category": "Cardiovascular", "symptom": "Dyspnea", "side_effect": "Urinary Tract Infection", "mechanism": "Promotes osmotic diuresis, reduces cardiac preload and afterload, and improves myocardial energetics.", "citation": "PMID:32865377"},
    {"drug": "Empagliflozin", "drug_class": "SGLT2 Inhibitor", "disease": "Chronic Kidney Disease", "disease_category": "Renal", "symptom": "Proteinuria", "side_effect": "Hypotension", "mechanism": "Restores tubuloglomerular feedback, lowering intraglomerular pressure and hyperfiltration.", "citation": "PMID:36331190"},

    # Dapagliflozin
    {"drug": "Dapagliflozin", "drug_class": "SGLT2 Inhibitor", "disease": "Type 2 Diabetes Mellitus", "disease_category": "Endocrine & Metabolic", "symptom": "Glucosuria", "side_effect": "Volume Depletion", "mechanism": "Blocks proximal tubule glucose reabsorption independently of insulin secretion.", "citation": "FDA-NDA-202293; PMID:24072873"},
    {"drug": "Dapagliflozin", "drug_class": "SGLT2 Inhibitor", "disease": "Heart Failure with Preserved Ejection Fraction", "disease_category": "Cardiovascular", "symptom": "Exercise Intolerance", "side_effect": "Euglycemic DKA", "mechanism": "Alleviates microvascular inflammation and improves cardiac diastolic filling.", "citation": "PMID:36027572"},
    {"drug": "Dapagliflozin", "drug_class": "SGLT2 Inhibitor", "disease": "Chronic Kidney Disease", "disease_category": "Renal", "symptom": "Declining eGFR", "side_effect": "Polyuria", "mechanism": "Slows rate of sustained eGFR loss and reduces risk of end-stage kidney disease.", "citation": "PMID:32970396"},

    # Sitagliptin
    {"drug": "Sitagliptin", "drug_class": "DPP-4 Inhibitor", "disease": "Type 2 Diabetes Mellitus", "disease_category": "Endocrine & Metabolic", "symptom": "Postprandial Hyperglycemia", "side_effect": "Nasopharyngitis", "mechanism": "Inhibits dipeptidyl peptidase-4 (DPP-4) degradation of endogenous incretins (GLP-1 and GIP).", "citation": "FDA-NDA-021995; PMID:17003251"},
    {"drug": "Sitagliptin", "drug_class": "DPP-4 Inhibitor", "disease": "Type 2 Diabetes Mellitus", "disease_category": "Endocrine & Metabolic", "symptom": "Hyperglycemia", "side_effect": "Joint Pain", "mechanism": "Prolongs active incretin hormone half-life, stimulating postprandial insulin release.", "citation": "PMID:26053366"},

    # Insulin Glargine
    {"drug": "Insulin Glargine", "drug_class": "Long-Acting Basal Insulin", "disease": "Type 1 Diabetes Mellitus", "disease_category": "Endocrine & Metabolic", "symptom": "Severe Hyperglycemia", "side_effect": "Hypoglycemia", "mechanism": "Forms microprecipitates in subcutaneous tissue providing flat, peakless 24-hour basal insulin profile.", "citation": "FDA-BLA-021081; PMID:10868846"},
    {"drug": "Insulin Glargine", "drug_class": "Long-Acting Basal Insulin", "disease": "Type 2 Diabetes Mellitus", "disease_category": "Endocrine & Metabolic", "symptom": "Fasting Hyperglycemia", "side_effect": "Lipodystrophy", "mechanism": "Promotes cellular uptake of glucose via tyrosine kinase insulin receptor activation.", "citation": "PMID:15616223"},

    # Glipizide
    {"drug": "Glipizide", "drug_class": "Second-Generation Sulfonylurea", "disease": "Type 2 Diabetes Mellitus", "disease_category": "Endocrine & Metabolic", "symptom": "Hyperglycemia", "side_effect": "Hypoglycemia", "mechanism": "Closes ATP-sensitive potassium channels in pancreatic beta cells, triggering membrane depolarization and insulin release.", "citation": "FDA-NDA-017783; PMID:2661845"},
    {"drug": "Glipizide", "drug_class": "Second-Generation Sulfonylurea", "disease": "Type 2 Diabetes Mellitus", "disease_category": "Endocrine & Metabolic", "symptom": "Polyuria", "side_effect": "Weight Gain", "mechanism": "Stimulates calcium influx through voltage-dependent channels to induce exocytosis of insulin granules.", "citation": "PMID:6219806"},

    # Lisinopril
    {"drug": "Lisinopril", "drug_class": "ACE Inhibitor", "disease": "Essential Hypertension", "disease_category": "Cardiovascular", "symptom": "Elevated Blood Pressure", "side_effect": "Dry Cough", "mechanism": "Competitively inhibits angiotensin-converting enzyme, preventing conversion of angiotensin I to angiotensin II and degrading bradykinin.", "citation": "FDA-NDA-019777; PMID:2743129"},
    {"drug": "Lisinopril", "drug_class": "ACE Inhibitor", "disease": "Congestive Heart Failure", "disease_category": "Cardiovascular", "symptom": "Peripheral Edema", "side_effect": "Hyperkalemia", "mechanism": "Suppresses aldosterone release, reducing total peripheral resistance and volume overload.", "citation": "PMID:10587334"},
    {"drug": "Lisinopril", "drug_class": "ACE Inhibitor", "disease": "Diabetic Nephropathy", "disease_category": "Renal", "symptom": "Albuminuria", "side_effect": "Angioedema", "mechanism": "Selectively dilates efferent arterioles, reducing glomerular capillary hydrostatic pressure.", "citation": "PMID:8247036"},

    # Losartan
    {"drug": "Losartan", "drug_class": "Angiotensin II Receptor Blocker (ARB)", "disease": "Essential Hypertension", "disease_category": "Cardiovascular", "symptom": "Elevated Blood Pressure", "side_effect": "Dizziness", "mechanism": "Blocks the binding of angiotensin II to AT1 receptors in vascular smooth muscle and adrenal gland.", "citation": "FDA-NDA-020386; PMID:7783335"},
    {"drug": "Losartan", "drug_class": "Angiotensin II Receptor Blocker (ARB)", "disease": "Diabetic Nephropathy", "disease_category": "Renal", "symptom": "Proteinuria", "side_effect": "Hyperkalemia", "mechanism": "Decreases intraglomerular pressure and retards progression of renal disease in diabetic patients.", "citation": "PMID:11565518"},
    {"drug": "Losartan", "drug_class": "Angiotensin II Receptor Blocker (ARB)", "disease": "Congestive Heart Failure", "disease_category": "Cardiovascular", "symptom": "Dyspnea on Exertion", "side_effect": "Hypotension", "mechanism": "Antagonizes AT1 receptor-mediated vasoconstriction and sympathetic activation.", "citation": "PMID:10609816"},

    # Amlodipine
    {"drug": "Amlodipine", "drug_class": "Dihydropyridine Calcium Channel Blocker", "disease": "Essential Hypertension", "disease_category": "Cardiovascular", "symptom": "Elevated Blood Pressure", "side_effect": "Peripheral Edema", "mechanism": "Inhibits transmembrane influx of extracellular calcium ions across myocardial and vascular smooth muscle membranes.", "citation": "FDA-NDA-019787; PMID:2528773"},
    {"drug": "Amlodipine", "drug_class": "Dihydropyridine Calcium Channel Blocker", "disease": "Chronic Stable Angina", "disease_category": "Cardiovascular", "symptom": "Chest Pain", "side_effect": "Flushing", "mechanism": "Dilates peripheral arterioles, decreasing myocardial oxygen demand and coronary vasospasm.", "citation": "PMID:1936306"},
    {"drug": "Amlodipine", "drug_class": "Dihydropyridine Calcium Channel Blocker", "disease": "Vasospastic Angina", "disease_category": "Cardiovascular", "symptom": "Resting Angina", "side_effect": "Headache", "mechanism": "Inhibits coronary artery smooth muscle constriction in response to vasospastic stimuli.", "citation": "PMID:7523171"},

    # Atorvastatin
    {"drug": "Atorvastatin", "drug_class": "HMG-CoA Reductase Inhibitor (Statin)", "disease": "Hypercholesterolemia", "disease_category": "Cardiovascular & Metabolic", "symptom": "Elevated LDL-C", "side_effect": "Myalgia", "mechanism": "Competitively inhibits 3-hydroxy-3-methylglutaryl-coenzyme A (HMG-CoA) reductase, upregulating hepatic LDL receptors.", "citation": "FDA-NDA-020702; PMID:9537248"},
    {"drug": "Atorvastatin", "drug_class": "HMG-CoA Reductase Inhibitor (Statin)", "disease": "Atherosclerotic Cardiovascular Disease", "disease_category": "Cardiovascular", "symptom": "Vascular Plaque", "side_effect": "Elevated Transaminases", "mechanism": "Exerts pleiotropic effects: plaque stabilization, improvement of endothelial function, anti-inflammatory actions.", "citation": "PMID:15024479"},
    {"drug": "Atorvastatin", "drug_class": "HMG-CoA Reductase Inhibitor (Statin)", "disease": "Coronary Artery Disease", "disease_category": "Cardiovascular", "symptom": "Angina Pectoris", "side_effect": "Rhabdomyolysis Risk", "mechanism": "Depletes mevalonate pathway intermediates, reducing vascular inflammation and smooth muscle proliferation.", "citation": "PMID:11252182"},

    # Rosuvastatin
    {"drug": "Rosuvastatin", "drug_class": "HMG-CoA Reductase Inhibitor (Statin)", "disease": "Hypercholesterolemia", "disease_category": "Cardiovascular & Metabolic", "symptom": "Elevated LDL-C", "side_effect": "Myalgia", "mechanism": "Hydrophilic statin with high selectivity for hepatic HMG-CoA reductase and low passive membrane permeability in muscle.", "citation": "FDA-NDA-021366; PMID:14564343"},
    {"drug": "Rosuvastatin", "drug_class": "HMG-CoA Reductase Inhibitor (Statin)", "disease": "Atherosclerotic Cardiovascular Disease", "disease_category": "Cardiovascular", "symptom": "Elevated hs-CRP", "side_effect": "Proteinuria", "mechanism": "Produces profound reductions in hs-CRP and regression of coronary atheroma volume.", "citation": "PMID:18997196"},

    # Metoprolol
    {"drug": "Metoprolol", "drug_class": "Beta-1 Selective Adrenergic Antagonist", "disease": "Essential Hypertension", "disease_category": "Cardiovascular", "symptom": "Elevated Blood Pressure", "side_effect": "Bradycardia", "mechanism": "Selectively antagonizes beta-1 adrenergic receptors in cardiac tissue, reducing heart rate and cardiac output.", "citation": "FDA-NDA-019974; PMID:6337583"},
    {"drug": "Metoprolol", "drug_class": "Beta-1 Selective Adrenergic Antagonist", "disease": "Heart Failure with Reduced Ejection Fraction", "disease_category": "Cardiovascular", "symptom": "Tachycardia", "side_effect": "Fatigue", "mechanism": "Protects myocardium from toxic effects of chronic sympathetic nervous system overactivation.", "citation": "PMID:10376614"},
    {"drug": "Metoprolol", "drug_class": "Beta-1 Selective Adrenergic Antagonist", "disease": "Angina Pectoris", "disease_category": "Cardiovascular", "symptom": "Exertional Chest Tightness", "side_effect": "Erectile Dysfunction", "mechanism": "Reduces rate-pressure product and myocardial oxygen consumption during physical exertion.", "citation": "PMID:3890886"},

    # Carvedilol
    {"drug": "Carvedilol", "drug_class": "Nonselective Beta and Alpha-1 Blocker", "disease": "Congestive Heart Failure", "disease_category": "Cardiovascular", "symptom": "Dyspnea on Exertion", "side_effect": "Orthostatic Hypotension", "mechanism": "Combines nonselective beta-adrenergic blockade with alpha-1 receptor-mediated peripheral vasodilation.", "citation": "FDA-NDA-020297; PMID:8622127"},
    {"drug": "Carvedilol", "drug_class": "Nonselective Beta and Alpha-1 Blocker", "disease": "Essential Hypertension", "disease_category": "Cardiovascular", "symptom": "Elevated Blood Pressure", "side_effect": "Dizziness", "mechanism": "Reduces systemic vascular resistance without significant reflex tachycardia or decreased renal blood flow.", "citation": "PMID:11434351"},

    # Apixaban
    {"drug": "Apixaban", "drug_class": "Direct Oral Anticoagulant (DOAC)", "disease": "Atrial Fibrillation", "disease_category": "Cardiovascular", "symptom": "Palpitations", "side_effect": "Major Bleeding", "mechanism": "Directly and reversibly inhibits free and clot-bound Factor Xa, suppressing prothrombinase activity.", "citation": "FDA-NDA-202155; PMID:21870978"},
    {"drug": "Apixaban", "drug_class": "Direct Oral Anticoagulant (DOAC)", "disease": "Deep Vein Thrombosis", "disease_category": "Cardiovascular & Hematologic", "symptom": "Lower Limb Swelling", "side_effect": "Bruising", "mechanism": "Prevents thrombin generation and subsequent fibrin clot formation without requiring antithrombin III.", "citation": "PMID:23447955"},
    {"drug": "Apixaban", "drug_class": "Direct Oral Anticoagulant (DOAC)", "disease": "Pulmonary Embolism", "disease_category": "Cardiovascular & Pulmonology", "symptom": "Pleuritic Chest Pain", "side_effect": "Gastrointestinal Bleed", "mechanism": "Halts ongoing thrombogenesis and reduces thrombus burden in pulmonary vascular tree.", "citation": "PMID:23812891"},

    # Warfarin
    {"drug": "Warfarin", "drug_class": "Vitamin K Antagonist", "disease": "Atrial Fibrillation", "disease_category": "Cardiovascular", "symptom": "Irregular Pulse", "side_effect": "Severe Hemorrhage", "mechanism": "Inhibits vitamin K epoxide reductase (VKORC1), preventing gamma-carboxylation of clotting factors II, VII, IX, and X.", "citation": "FDA-NDA-009218; PMID:14966050"},
    {"drug": "Warfarin", "drug_class": "Vitamin K Antagonist", "disease": "Prosthetic Heart Valve Thrombosis", "disease_category": "Cardiovascular", "symptom": "Thromboembolism", "side_effect": "Warfarin-Induced Skin Necrosis", "mechanism": "Depletes vitamin K-dependent procoagulant factors to prolong international normalized ratio (INR).", "citation": "PMID:8192667"},

    # Albuterol
    {"drug": "Albuterol", "drug_class": "Short-Acting Beta-2 Agonist (SABA)", "disease": "Asthma", "disease_category": "Respiratory", "symptom": "Wheezing", "side_effect": "Tremor", "mechanism": "Stimulates beta-2 adrenergic receptors on airway smooth muscle, activating adenylate cyclase and relaxing bronchial smooth muscle.", "citation": "FDA-NDA-019489; PMID:11738517"},
    {"drug": "Albuterol", "drug_class": "Short-Acting Beta-2 Agonist (SABA)", "disease": "Asthma", "disease_category": "Respiratory", "symptom": "Shortness of Breath", "side_effect": "Palpitations", "mechanism": "Rapid bronchodilation within 5 minutes of inhalation via cyclic AMP-mediated calcium extrusion.", "citation": "PMID:8482431"},
    {"drug": "Albuterol", "drug_class": "Short-Acting Beta-2 Agonist (SABA)", "disease": "Chronic Obstructive Pulmonary Disease", "disease_category": "Respiratory", "symptom": "Dyspnea", "side_effect": "Tachycardia", "mechanism": "Relieves acute bronchospasm and dynamic pulmonary hyperinflation in COPD exacerbations.", "citation": "PMID:15961603"},

    # Fluticasone
    {"drug": "Fluticasone", "drug_class": "Inhaled Corticosteroid", "disease": "Asthma", "disease_category": "Respiratory", "symptom": "Airway Inflammation", "side_effect": "Oral Candidiasis", "mechanism": "Translocates into the nucleus to inhibit transcription factors NF-kB and AP-1, suppressing cytokine synthesis.", "citation": "FDA-NDA-021433; PMID:9577937"},
    {"drug": "Fluticasone", "drug_class": "Inhaled Corticosteroid", "disease": "Allergic Rhinitis", "disease_category": "Respiratory & Immunology", "symptom": "Rhinorrhea", "side_effect": "Epistaxis", "mechanism": "Inhibits mucosal mast cell degranulation, eosinophil recruitment, and inflammatory mediator release.", "citation": "PMID:10724300"},
    {"drug": "Fluticasone", "drug_class": "Inhaled Corticosteroid", "disease": "Chronic Obstructive Pulmonary Disease", "disease_category": "Respiratory", "symptom": "Frequent Exacerbations", "side_effect": "Dysphonia", "mechanism": "Attenuates airway mucosal inflammation and decreases inflammatory cell infiltration.", "citation": "PMID:17314337"},

    # Budesonide
    {"drug": "Budesonide", "drug_class": "Inhaled / Gut-Targeted Glucocorticoid", "disease": "Asthma", "disease_category": "Respiratory", "symptom": "Nocturnal Cough", "side_effect": "Throat Irritation", "mechanism": "Exerts high local glucocorticoid receptor affinity with extensive first-pass hepatic metabolism limiting systemic bioavailability.", "citation": "FDA-NDA-020929; PMID:10793786"},
    {"drug": "Budesonide", "drug_class": "Inhaled / Gut-Targeted Glucocorticoid", "disease": "Crohn's Disease", "disease_category": "Gastroenterology", "symptom": "Ileal Inflammation", "side_effect": "Cushingoid Features", "mechanism": "Controlled ileal release delivers potent topically active corticosteroid directly to terminal ileum.", "citation": "PMID:15846624"},

    # Montelukast
    {"drug": "Montelukast", "drug_class": "Leukotriene Receptor Antagonist", "disease": "Asthma", "disease_category": "Respiratory", "symptom": "Bronchoconstriction", "side_effect": "Neuropsychiatric Events", "mechanism": "Selectively antagonizes cysteinyl leukotriene CysLT1 receptors, blocking LTD4-induced airway smooth muscle spasm.", "citation": "FDA-NDA-020829; PMID:9876274"},
    {"drug": "Montelukast", "drug_class": "Leukotriene Receptor Antagonist", "disease": "Allergic Rhinitis", "disease_category": "Respiratory & Immunology", "symptom": "Nasal Congestion", "side_effect": "Headache", "mechanism": "Blocks leukotriene-mediated vascular permeability and mucus hypersecretion in nasal passages.", "citation": "PMID:11827474"},

    # Sertraline
    {"drug": "Sertraline", "drug_class": "Selective Serotonin Reuptake Inhibitor (SSRI)", "disease": "Major Depressive Disorder", "disease_category": "Psychiatry", "symptom": "Anhedonia", "side_effect": "Sexual Dysfunction", "mechanism": "Potently inhibits serotonin transporter (SERT) reuptake, enhancing synaptic 5-HT availability.", "citation": "FDA-NDA-019839; PMID:1603096"},
    {"drug": "Sertraline", "drug_class": "Selective Serotonin Reuptake Inhibitor (SSRI)", "disease": "Generalized Anxiety Disorder", "disease_category": "Psychiatry", "symptom": "Excessive Worry", "side_effect": "Insomnia", "mechanism": "Desensitizes 5-HT1A auto-receptors in raphe nuclei, facilitating sustained serotonergic neurotransmission.", "citation": "PMID:12401735"},
    {"drug": "Sertraline", "drug_class": "Selective Serotonin Reuptake Inhibitor (SSRI)", "disease": "Obsessive-Compulsive Disorder", "disease_category": "Psychiatry", "symptom": "Intrusive Thoughts", "side_effect": "Nausea", "mechanism": "Modulates cortico-striato-thalamo-cortical (CSTC) neurocircuitry through persistent serotonergic modulation.", "citation": "PMID:8601362"},
    {"drug": "Sertraline", "drug_class": "Selective Serotonin Reuptake Inhibitor (SSRI)", "disease": "Post-Traumatic Stress Disorder", "disease_category": "Psychiatry", "symptom": "Flashbacks", "side_effect": "Tremor", "mechanism": "Rebalances amygdala hyperreactivity and prefrontal hypoactivity in emotional regulation circuits.", "citation": "PMID:10757755"},

    # Escitalopram
    {"drug": "Escitalopram", "drug_class": "Selective Serotonin Reuptake Inhibitor (SSRI)", "disease": "Major Depressive Disorder", "disease_category": "Psychiatry", "symptom": "Depressed Mood", "side_effect": "Somnolence", "mechanism": "Pure S-enantiomer exhibiting allosteric serotonin transporter binding with high target selectivity.", "citation": "FDA-NDA-021323; PMID:12044195"},
    {"drug": "Escitalopram", "drug_class": "Selective Serotonin Reuptake Inhibitor (SSRI)", "disease": "Panic Disorder", "disease_category": "Psychiatry", "symptom": "Panic Attacks", "side_effect": "Sweating", "mechanism": "Downregulates locus coeruleus noradrenergic hyper-responsiveness via serotonergic feedback.", "citation": "PMID:15055233"},

    # Duloxetine
    {"drug": "Duloxetine", "drug_class": "Serotonin-Norepinephrine Reuptake Inhibitor (SNRI)", "disease": "Major Depressive Disorder", "disease_category": "Psychiatry", "symptom": "Psychomotor Retardation", "side_effect": "Nausea", "mechanism": "Dual inhibition of neuronal serotonin (SERT) and norepinephrine (NET) reuptake transporters.", "citation": "FDA-NDA-021427; PMID:15234909"},
    {"drug": "Duloxetine", "drug_class": "Serotonin-Norepinephrine Reuptake Inhibitor (SNRI)", "disease": "Diabetic Peripheral Neuropathic Pain", "disease_category": "Neurology & Pain", "symptom": "Burning Neuropathic Pain", "side_effect": "Dry Mouth", "mechanism": "Enhances descending inhibitory noradrenergic and serotonergic pain pathways in spinal cord dorsal horn.", "citation": "PMID:16140730"},
    {"drug": "Duloxetine", "drug_class": "Serotonin-Norepinephrine Reuptake Inhibitor (SNRI)", "disease": "Fibromyalgia", "disease_category": "Rheumatology & Pain", "symptom": "Diffuse Musculoskeletal Pain", "side_effect": "Constipation", "mechanism": "Reconditions central pain sensitization and neurotransmitter deficits in central nervous system.", "citation": "PMID:18497676"},

    # Levodopa
    {"drug": "Levodopa", "drug_class": "Dopamine Precursor", "disease": "Parkinson's Disease", "disease_category": "Neurology", "symptom": "Bradykinesia", "side_effect": "Dyskinesia", "mechanism": "Crosses the blood-brain barrier via large neutral amino acid transporter (LAT1) and decarboxylates into dopamine.", "citation": "FDA-NDA-016834; PMID:5417436"},
    {"drug": "Levodopa", "drug_class": "Dopamine Precursor", "disease": "Parkinson's Disease", "disease_category": "Neurology", "symptom": "Resting Tremor", "side_effect": "Orthostatic Hypotension", "mechanism": "Replenishes striatal dopamine deficiency caused by substantia nigra pars compacta neurodegeneration.", "citation": "PMID:15610816"},
    {"drug": "Levodopa", "drug_class": "Dopamine Precursor", "disease": "Parkinson's Disease", "disease_category": "Neurology", "symptom": "Muscle Rigidity", "side_effect": "Visual Hallucinations", "mechanism": "Restores basal ganglia direct pathway output, alleviating motor dysfunction.", "citation": "PMID:11986445"},

    # Donepezil
    {"drug": "Donepezil", "drug_class": "Acetylcholinesterase Inhibitor", "disease": "Alzheimer's Disease", "disease_category": "Neurology", "symptom": "Cognitive Decline", "side_effect": "Bradycardia", "mechanism": "Reversibly inhibits acetylcholinesterase, prolonging the action of acetylcholine at central cholinergic synapses.", "citation": "FDA-NDA-020655; PMID:9786431"},
    {"drug": "Donepezil", "drug_class": "Acetylcholinesterase Inhibitor", "disease": "Alzheimer's Disease", "disease_category": "Neurology", "symptom": "Memory Loss", "side_effect": "Diarrhea", "mechanism": "Compensates for the progressive loss of basal forebrain cholinergic neurons in early-to-moderate dementia.", "citation": "PMID:11346369"},

    # Memantine
    {"drug": "Memantine", "drug_class": "NMDA Receptor Antagonist", "disease": "Alzheimer's Disease", "disease_category": "Neurology", "symptom": "Severe Cognitive Impairment", "side_effect": "Confusion", "mechanism": "Uncompetitive, low-affinity NMDA open-channel blocker that prevents excitotoxic glutamate signaling.", "citation": "FDA-NDA-021487; PMID:12672858"},
    {"drug": "Memantine", "drug_class": "NMDA Receptor Antagonist", "disease": "Alzheimer's Disease", "disease_category": "Neurology", "symptom": "Disorientation", "side_effect": "Dizziness", "mechanism": "Preserves physiological glutamate transmission required for long-term potentiation and memory formation.", "citation": "PMID:15649964"},

    # Gabapentin
    {"drug": "Gabapentin", "drug_class": "Alpha-2-Delta Ligand", "disease": "Neuropathic Pain", "disease_category": "Neurology & Pain", "symptom": "Hyperalgesia", "side_effect": "Somnolence", "mechanism": "Binds high-affinity alpha-2-delta auxiliary subunits of voltage-gated calcium channels, attenuating neurotransmitter exocytosis.", "citation": "FDA-NDA-020235; PMID:9847116"},
    {"drug": "Gabapentin", "drug_class": "Alpha-2-Delta Ligand", "disease": "Focal Seizures", "disease_category": "Neurology", "symptom": "Involuntary Muscle Spasms", "side_effect": "Dizziness", "mechanism": "Reduces presynaptic release of glutamate, substance P, and calcitonin gene-related peptide (CGRP).", "citation": "PMID:8243144"},
    {"drug": "Gabapentin", "drug_class": "Alpha-2-Delta Ligand", "disease": "Postherpetic Neuralgia", "disease_category": "Neurology & Pain", "symptom": "Allodynia", "side_effect": "Peripheral Edema", "mechanism": "Suppresses hyperexcitable spinal dorsal horn neurons following varicella-zoster virus nerve injury.", "citation": "PMID:9851887"},

    # Pregabalin
    {"drug": "Pregabalin", "drug_class": "Alpha-2-Delta Ligand", "disease": "Neuropathic Pain", "disease_category": "Neurology & Pain", "symptom": "Burning Sensation", "side_effect": "Weight Gain", "mechanism": "High-affinity modulator of P/Q-type calcium channel trafficking, reducing excitatory spinal neurotransmitter release.", "citation": "FDA-NDA-021446; PMID:15234911"},
    {"drug": "Pregabalin", "drug_class": "Alpha-2-Delta Ligand", "disease": "Fibromyalgia", "disease_category": "Rheumatology & Pain", "symptom": "Widespread Pain", "side_effect": "Ataxia", "mechanism": "Attenuates central nervous system hyperexcitability and sensory processing amplification.", "citation": "PMID:18497679"},

    # Sumatriptan
    {"drug": "Sumatriptan", "drug_class": "5-HT1B/1D Receptor Agonist (Triptan)", "disease": "Migraine", "disease_category": "Neurology", "symptom": "Unilateral Throbbing Headache", "side_effect": "Chest Tightness", "mechanism": "Constricts meningeal and cerebral blood vessels via 5-HT1B receptors and inhibits trigeminal sensory nerve activation via 5-HT1D receptors.", "citation": "FDA-NDA-020080; PMID:1653139"},
    {"drug": "Sumatriptan", "drug_class": "5-HT1B/1D Receptor Agonist (Triptan)", "disease": "Migraine", "disease_category": "Neurology", "symptom": "Photophobia", "side_effect": "Paresthesia", "mechanism": "Blocks presynaptic release of vasoactive neuropeptides including CGRP from trigeminovascular terminals.", "citation": "PMID:18070094"},
    {"drug": "Sumatriptan", "drug_class": "5-HT1B/1D Receptor Agonist (Triptan)", "disease": "Cluster Headache", "disease_category": "Neurology", "symptom": "Periorbital Piercing Pain", "side_effect": "Coronary Vasospasm Risk", "mechanism": "Terminates neurogenic cranial vasodilatation and trigeminal autonomic reflex discharge.", "citation": "PMID:8243149"},

    # Methotrexate
    {"drug": "Methotrexate", "drug_class": "Antifolate DMARD", "disease": "Rheumatoid Arthritis", "disease_category": "Rheumatology & Autoimmune", "symptom": "Joint Pain and Swelling", "side_effect": "Hepatotoxicity", "mechanism": "Inhibits dihydrofolate reductase (DHFR) and aminoimidazolecarboxamide ribonucleotide (AICAR) transformylase, leading to extracellular adenosine accumulation.", "citation": "FDA-NDA-011719; PMID:15234909"},
    {"drug": "Methotrexate", "drug_class": "Antifolate DMARD", "disease": "Plaque Psoriasis", "disease_category": "Dermatology", "symptom": "Erythematous Scaly Plaques", "side_effect": "Bone Marrow Suppression", "mechanism": "Inhibits DNA synthesis in rapidly dividing keratinocytes and suppresses activated T-lymphocyte proliferation.", "citation": "PMID:12702061"},
    {"drug": "Methotrexate", "drug_class": "Antifolate DMARD", "disease": "Psoriatic Arthritis", "disease_category": "Rheumatology & Autoimmune", "symptom": "Dactylitis", "side_effect": "Stomatitis", "mechanism": "Suppresses dihydrofolate reduction and lowers cytokine production (TNF, IL-1).", "citation": "PMID:10724305"},

    # Adalimumab
    {"drug": "Adalimumab", "drug_class": "Anti-TNF Monoclonal Antibody", "disease": "Rheumatoid Arthritis", "disease_category": "Rheumatology & Autoimmune", "symptom": "Morning Joint Stiffness", "side_effect": "Serious Infection Risk", "mechanism": "Specifically binds soluble and membrane-bound TNF-alpha, preventing interaction with p55 and p75 cell surface receptors.", "citation": "FDA-BLA-125057; PMID:12687508"},
    {"drug": "Adalimumab", "drug_class": "Anti-TNF Monoclonal Antibody", "disease": "Crohn's Disease", "disease_category": "Gastroenterology", "symptom": "Abdominal Pain", "side_effect": "Injection Site Reaction", "mechanism": "Induces apoptosis of transmembrane TNF-bearing inflammatory cells, dampening transmural intestinal inflammation.", "citation": "PMID:17298758"},
    {"drug": "Adalimumab", "drug_class": "Anti-TNF Monoclonal Antibody", "disease": "Ulcerative Colitis", "disease_category": "Gastroenterology", "symptom": "Bloody Diarrhea", "side_effect": "Tuberculosis Reactivation Risk", "mechanism": "Neutralizes intestinal mucosal TNF-alpha bioactivity and decreases leukocyte extravasation.", "citation": "PMID:22266897"},
    {"drug": "Adalimumab", "drug_class": "Anti-TNF Monoclonal Antibody", "disease": "Ankylosing Spondylitis", "disease_category": "Rheumatology & Autoimmune", "symptom": "Inflammatory Back Pain", "side_effect": "Demyelinating Disease Risk", "mechanism": "Reduces spinal enthesitis and osteoclast activation mediated by TNF superfamily pathways.", "citation": "PMID:16531398"},

    # Infliximab
    {"drug": "Infliximab", "drug_class": "Chimeric Anti-TNF Monoclonal Antibody", "disease": "Crohn's Disease", "disease_category": "Gastroenterology", "symptom": "Fistula Formation", "side_effect": "Infusion Reactions", "mechanism": "High-affinity binding of soluble and transmembrane TNF-alpha, lysing target cells via complement-dependent cytotoxicity.", "citation": "FDA-BLA-103772; PMID:9321530"},
    {"drug": "Infliximab", "drug_class": "Chimeric Anti-TNF Monoclonal Antibody", "disease": "Rheumatoid Arthritis", "disease_category": "Rheumatology & Autoimmune", "symptom": "Synovial Proliferation", "side_effect": "Opportunistic Fungal Infections", "mechanism": "Reverses elevated serum IL-6 and matrix metalloproteinase-3 levels in arthritic joints.", "citation": "PMID:10609819"},

    # Pembrolizumab
    {"drug": "Pembrolizumab", "drug_class": "Immune Checkpoint Inhibitor (PD-1 Blocker)", "disease": "Melanoma", "disease_category": "Oncology", "symptom": "Malignant Skin Lesion", "side_effect": "Immune-Mediated Colitis", "mechanism": "Selectively binds PD-1 receptor on cytotoxic T-cells, preventing engagement with PD-L1/PD-L2 and reactivating antitumor immunity.", "citation": "FDA-BLA-125514; PMID:25891304"},
    {"drug": "Pembrolizumab", "drug_class": "Immune Checkpoint Inhibitor (PD-1 Blocker)", "disease": "Non-Small Cell Lung Cancer", "disease_category": "Oncology", "symptom": "Hemoptysis", "side_effect": "Immune-Mediated Pneumonitis", "mechanism": "Restores tumor-infiltrating lymphocyte effector function against tumor neoantigens.", "citation": "PMID:27718847"},
    {"drug": "Pembrolizumab", "drug_class": "Immune Checkpoint Inhibitor (PD-1 Blocker)", "disease": "Head and Neck Squamous Cell Carcinoma", "disease_category": "Oncology", "symptom": "Neck Mass", "side_effect": "Thyroiditis", "mechanism": "Blocks T-cell checkpoint exhaust pathway in recurrent/metastatic microsatellite-high malignancies.", "citation": "PMID:31679945"},

    # Imatinib
    {"drug": "Imatinib", "drug_class": "Tyrosine Kinase Inhibitor (BCR-ABL)", "disease": "Chronic Myeloid Leukemia", "disease_category": "Oncology & Hematology", "symptom": "Splenomegaly", "side_effect": "Fluid Retention", "mechanism": "Competitively binds ATP-binding pocket of BCR-ABL oncoprotein, arresting leukemic cell proliferation.", "citation": "FDA-NDA-021335; PMID:11287951"},
    {"drug": "Imatinib", "drug_class": "Tyrosine Kinase Inhibitor (BCR-ABL)", "disease": "Gastrointestinal Stromal Tumor", "disease_category": "Oncology", "symptom": "Abdominal Mass", "side_effect": "Nausea", "mechanism": "Selectively inhibits KIT (CD117) and PDGF receptor tyrosine kinase signaling.", "citation": "PMID:11932470"},

    # Tamoxifen
    {"drug": "Tamoxifen", "drug_class": "Selective Estrogen Receptor Modulator (SERM)", "disease": "Breast Cancer (ER-Positive)", "disease_category": "Oncology", "symptom": "Breast Lump", "side_effect": "Hot Flashes", "mechanism": "Competitively antagonizes estrogen binding to estrogen receptors in mammary gland tissue.", "citation": "FDA-NDA-017970; PMID:9786435"},
    {"drug": "Tamoxifen", "drug_class": "Selective Estrogen Receptor Modulator (SERM)", "disease": "Breast Cancer (ER-Positive)", "disease_category": "Oncology", "symptom": "Nipple Discharge", "side_effect": "Thromboembolism Risk", "mechanism": "Inhibits G1 phase cell-cycle progression in estrogen-dependent neoplastic breast epithelium.", "citation": "PMID:10376618"},

    # Omeprazole
    {"drug": "Omeprazole", "drug_class": "Proton Pump Inhibitor (PPI)", "disease": "Gastroesophageal Reflux Disease", "disease_category": "Gastroenterology", "symptom": "Heartburn", "side_effect": "Hypomagnesemia", "mechanism": "Covalently binds cysteine residues of H+/K+ ATPase in gastric parietal cells, shutting down basal and stimulated gastric acid production.", "citation": "FDA-NDA-019810; PMID:2167448"},
    {"drug": "Omeprazole", "drug_class": "Proton Pump Inhibitor (PPI)", "disease": "Peptic Ulcer Disease", "disease_category": "Gastroenterology", "symptom": "Epigastric Pain", "side_effect": "Clostridium difficile Infection Risk", "mechanism": "Sustains intragastric pH above 4.0, allowing mucosal epithelial repair and healing of duodenal and gastric craters.", "citation": "PMID:1709405"},
    {"drug": "Omeprazole", "drug_class": "Proton Pump Inhibitor (PPI)", "disease": "Zollinger-Ellison Syndrome", "disease_category": "Gastroenterology", "symptom": "Severe Hyperacidity", "side_effect": "Bone Fracture Risk", "mechanism": "Suppresses pathological gastric acid hypersecretion driven by autonomous gastrinomas.", "citation": "PMID:24072879"},

    # Pantoprazole
    {"drug": "Pantoprazole", "drug_class": "Proton Pump Inhibitor (PPI)", "disease": "Gastroesophageal Reflux Disease", "disease_category": "Gastroenterology", "symptom": "Acid Regurgitation", "side_effect": "Headache", "mechanism": "Selective binding to Cys822 of proton pump with low CYP2C19 interaction potential.", "citation": "FDA-NDA-020987; PMID:10793789"},
    {"drug": "Pantoprazole", "drug_class": "Proton Pump Inhibitor (PPI)", "disease": "Erosive Esophagitis", "disease_category": "Gastroenterology", "symptom": "Odynophagia", "side_effect": "Diarrhea", "mechanism": "Promotes rapid endoscopic mucosal re-epithelialization of esophageal ulcerations.", "citation": "PMID:12401739"},

    # Amoxicillin
    {"drug": "Amoxicillin", "drug_class": "Aminopenicillin Antibiotic", "disease": "Streptococcal Pharyngitis", "disease_category": "Infectious Disease", "symptom": "Sore Throat", "side_effect": "Maculopapular Rash", "mechanism": "Inactivates penicillin-binding proteins (PBPs) involved in peptidoglycan crosslinking, triggering osmotic bacterial cell lysis.", "citation": "FDA-NDA-050542; PMID:6390822"},
    {"drug": "Amoxicillin", "drug_class": "Aminopenicillin Antibiotic", "disease": "Acute Otitis Media", "disease_category": "Infectious Disease", "symptom": "Otalgia", "side_effect": "Diarrhea", "mechanism": "Broad bactericidal activity against Streptococcus pneumoniae and Haemophilus influenzae strains.", "citation": "PMID:11520976"},
    {"drug": "Amoxicillin", "drug_class": "Aminopenicillin Antibiotic", "disease": "Community-Acquired Pneumonia", "disease_category": "Infectious Disease", "symptom": "Productive Cough", "side_effect": "Allergic Anaphylaxis", "mechanism": "Penetrates bronchial secretions to achieve bactericidal concentrations against respiratory pathogens.", "citation": "PMID:17924869"},

    # Ciprofloxacin
    {"drug": "Ciprofloxacin", "drug_class": "Fluoroquinolone Antibiotic", "disease": "Complicated Urinary Tract Infection", "disease_category": "Infectious Disease", "symptom": "Dysuria", "side_effect": "Tendon Rupture Risk", "mechanism": "Inhibits bacterial DNA gyrase (topoisomerase II) and topoisomerase IV, causing double-stranded DNA breaks and bactericidal death.", "citation": "FDA-NDA-019537; PMID:2890458"},
    {"drug": "Ciprofloxacin", "drug_class": "Fluoroquinolone Antibiotic", "disease": "Infectious Diarrhea", "disease_category": "Infectious Disease", "symptom": "Abdominal Cramps", "side_effect": "QT Prolongation", "mechanism": "Rapidly achieves high bactericidal tissue concentrations in gastrointestinal mucosa and urogenital tract.", "citation": "PMID:3300588"},
    {"drug": "Ciprofloxacin", "drug_class": "Fluoroquinolone Antibiotic", "disease": "Acute Pyelonephritis", "disease_category": "Infectious Disease", "symptom": "Flank Pain", "side_effect": "CNS Toxicity", "mechanism": "Eradicates gram-negative bacilli such as E. coli in renal parenchyma.", "citation": "PMID:10587339"},

    # Doxycycline
    {"drug": "Doxycycline", "drug_class": "Tetracycline Antibiotic", "disease": "Lyme Disease", "disease_category": "Infectious Disease", "symptom": "Erythema Migrans", "side_effect": "Photosensitivity", "mechanism": "Reversibly binds the 30S ribosomal subunit, preventing aminoacyl-tRNA association and halting bacterial protein synthesis.", "citation": "FDA-NDA-050444; PMID:9208447"},
    {"drug": "Doxycycline", "drug_class": "Tetracycline Antibiotic", "disease": "Acne Vulgaris", "disease_category": "Dermatology", "symptom": "Inflammatory Papules", "side_effect": "Esophageal Irritation", "mechanism": "Exerts anti-inflammatory actions through matrix metalloproteinase inhibition and decreases Cutibacterium acnes bacterial load.", "citation": "PMID:17518471"},
    {"drug": "Doxycycline", "drug_class": "Tetracycline Antibiotic", "disease": "Community-Acquired Pneumonia", "disease_category": "Infectious Disease", "symptom": "Fever and Chills", "side_effect": "Tooth Discoloration (Children)", "mechanism": "Bacteriostatic inhibition against atypical respiratory pathogens (Mycoplasma, Chlamydophila).", "citation": "PMID:11986449"},

    # Azithromycin
    {"drug": "Azithromycin", "drug_class": "Macrolide Antibiotic", "disease": "Community-Acquired Pneumonia", "disease_category": "Infectious Disease", "symptom": "Shortness of Breath", "side_effect": "QT Interval Prolongation", "mechanism": "Reversibly binds to 50S ribosomal subunit, preventing peptide translocation during bacterial protein elongation.", "citation": "FDA-NDA-050670; PMID:8482436"},
    {"drug": "Azithromycin", "drug_class": "Macrolide Antibiotic", "disease": "Acute Bacterial Sinusitis", "disease_category": "Infectious Disease", "symptom": "Facial Pain", "side_effect": "Diarrhea", "mechanism": "Accumulates inside alveolar macrophages and delivers high sustained tissue concentrations.", "citation": "PMID:11738521"},

    # Paxlovid
    {"drug": "Paxlovid", "drug_class": "Viral Protease Inhibitor", "disease": "COVID-19", "disease_category": "Infectious Disease", "symptom": "Fever", "side_effect": "Dysgeusia (Metallic Taste)", "mechanism": "Nirmatrelvir potently inhibits SARS-CoV-2 main protease (Mpro/3CLpro); ritonavir acts as a pharmacokinetic booster via CYP3A inhibition.", "citation": "FDA-EUA-106; PMID:35172054"},
    {"drug": "Paxlovid", "drug_class": "Viral Protease Inhibitor", "disease": "COVID-19", "disease_category": "Infectious Disease", "symptom": "Cough", "side_effect": "CYP3A Drug-Drug Interactions", "mechanism": "Prevents cleavage of polyprotein precursors essential for viral replication cycle.", "citation": "PMID:35172054"},
    {"drug": "Paxlovid", "drug_class": "Viral Protease Inhibitor", "disease": "COVID-19", "disease_category": "Infectious Disease", "symptom": "Loss of Taste or Smell", "side_effect": "Elevated Blood Pressure", "mechanism": "Rapidly suppresses viral shedding within 48 to 72 hours of treatment onset.", "citation": "PMID:35472899"},

    # Ibuprofen
    {"drug": "Ibuprofen", "drug_class": "Nonsteroidal Anti-inflammatory Drug (NSAID)", "disease": "Osteoarthritis", "disease_category": "Rheumatology & Musculoskeletal", "symptom": "Joint Stiffness", "side_effect": "Gastric Ulceration", "mechanism": "Nonselectively inhibits cyclooxygenase isoforms COX-1 and COX-2, decreasing prostaglandin E2 (PGE2) synthesis.", "citation": "FDA-NDA-017463; PMID:3890889"},
    {"drug": "Ibuprofen", "drug_class": "Nonsteroidal Anti-inflammatory Drug (NSAID)", "disease": "Tension Headache", "disease_category": "Neurology", "symptom": "Constricting Head Pain", "side_effect": "Renal Impairment", "mechanism": "Inhibits peripheral pain receptor sensitization and central prostaglandin-mediated nociception.", "citation": "PMID:8247039"},

    # Celecoxib
    {"drug": "Celecoxib", "drug_class": "Selective COX-2 Inhibitor", "disease": "Osteoarthritis", "disease_category": "Rheumatology & Musculoskeletal", "symptom": "Joint Crepitus", "side_effect": "Cardiovascular Thrombotic Risk", "mechanism": "Selectively inhibits cyclooxygenase-2 (COX-2) sparing platelet COX-1, reducing inflammatory prostanoids without gastrointestinal ulceration.", "citation": "FDA-NDA-020998; PMID:10499703"},
    {"drug": "Celecoxib", "drug_class": "Selective COX-2 Inhibitor", "disease": "Ankylosing Spondylitis", "disease_category": "Rheumatology & Autoimmune", "symptom": "Spinal Rigidity", "side_effect": "Fluid Retention", "mechanism": "Dampens synovial and periarticular bone inflammation without antiplatelet bleeding tendencies.", "citation": "PMID:11565522"},

    # Colchicine
    {"drug": "Colchicine", "drug_class": "Microtubule Disassembly Inhibitor", "disease": "Gout Flares", "disease_category": "Rheumatology & Metabolic", "symptom": "Severe Podagra", "side_effect": "Severe Diarrhea", "mechanism": "Binds tubulin heterodimers preventing microtubule polymer assembly, blocking neutrophil chemotaxis and NLRP3 inflammasome activation.", "citation": "FDA-NDA-022352; PMID:20444988"},
    {"drug": "Colchicine", "drug_class": "Microtubule Disassembly Inhibitor", "disease": "Pericarditis", "disease_category": "Cardiovascular", "symptom": "Positional Chest Pain", "side_effect": "Abdominal Cramping", "mechanism": "Inhibits interleukin-1beta production and reduces recurrent pericardial inflammation.", "citation": "PMID:24072881"}
]

# Write CSV
csv_path = "data/biomedical_dataset.csv"
fieldnames = ["drug_name", "drug_class", "disease_name", "disease_category", "symptom_name", "side_effect_name", "mechanism_of_action", "citation"]
with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for r in records:
        writer.writerow({
            "drug_name": r["drug"],
            "drug_class": r["drug_class"],
            "disease_name": r["disease"],
            "disease_category": r["disease_category"],
            "symptom_name": r["symptom"],
            "side_effect_name": r["side_effect"],
            "mechanism_of_action": r["mechanism"],
            "citation": r["citation"]
        })

print(f"Generated {len(records)} biomedical records into {csv_path}")

# Write comprehensive drug monographs for vector RAG
monographs = []
drugs_seen = set()
for r in records:
    d = r["drug"]
    if d not in drugs_seen:
        drugs_seen.add(d)
        indications = sorted(list(set([rec["disease"] for rec in records if rec["drug"] == d])))
        symptoms = sorted(list(set([rec["symptom"] for rec in records if rec["drug"] == d])))
        side_effects = sorted(list(set([rec["side_effect"] for rec in records if rec["drug"] == d])))
        citations = sorted(list(set([rec["citation"] for rec in records if rec["drug"] == d])))
        
        monograph = {
            "drug_name": d,
            "drug_class": r["drug_class"],
            "indications": indications,
            "common_symptoms_treated": symptoms,
            "key_side_effects": side_effects,
            "mechanism_description": f"{d} belongs to the class of {r['drug_class']}. Mechanism of Action: {r['mechanism']}",
            "pharmacology_summary": (
                f"### Monograph: {d} ({r['drug_class']})\n"
                f"- **Clinical Indications:** {', '.join(indications)}.\n"
                f"- **Target Symptoms:** {', '.join(symptoms)}.\n"
                f"- **Pharmacological Action & Pathway:** {r['mechanism']}\n"
                f"- **Known Adverse Reactions & Warnings:** {', '.join(side_effects)}.\n"
                f"- **Evidence & Citations:** {'; '.join(citations)}."
            ),
            "citations": citations
        }
        monographs.append(monograph)

json_path = "data/drug_monographs.json"
with open(json_path, mode="w", encoding="utf-8") as f:
    json.dump(monographs, f, indent=2)

print(f"Generated {len(monographs)} comprehensive drug monographs into {json_path}")
