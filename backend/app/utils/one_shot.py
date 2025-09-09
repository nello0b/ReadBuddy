import random
from typing import Tuple, List
import textwrap
from app.utils.prompt_builder import PromptBuilder
from app.utils.parse_response import parse_json_or_key_value_fallback



MCQ_CREATION_TASK = """Task:
        Generate one multiple-choice question (MCQ) based on the article. Use the glossary to resolve terms.
        Consider that  the person answering the question does not have access to the article, so the question should be very complete.
        Write the question and options in the same language as the article."""
        
MCQ_REVIEW_TASK = """Task:
        Consider the article and the glossary, and review the weaknesses of the following multiple-choice question (MCQ), according to the following criteria:
        1. Format: The question should be in a JSON format with the following keys:
           - question (string type)
           - options (dictionary with string keys "1"-"5" and string values)
           - correct_answer (string key)
           - chain_of_thought (string type, and optional)
        2. Language: The question and options should be in the same language as the article. The language used should be clear and appropriate for the target audience.
        3. Grammar: The question should be grammatically correct and free of spelling mistakes.
        4. Relevance: The question should be relevant to the article and the glossary. Avoid questions that:
           A) Focus on isolated facts or statistics.
           B) Require rote memorization of numbers or minor details which are not central to the article's main themes.
           C) Could be answered without understanding broader themes.
           D) Cannot be reasonably answered without direct access to the article.
           Prefer questions that assess understanding of relationships, definitions, ideas, or major claims.
        5. Correctness: The question should have a correct answer that is clearly supported by the article and the glossary.

        Give the question a score from 1 to 10 in each of the criteria.
        For each score under 10, provide reasoning. For a score of 10, DO NOT INCLUDE REASONING.
        Be very critical and analytical don't sweeten the review."""

ARTICALES = {
    # 1) Origin of the name Judaism
    "Origin_of_the_name_Judaism" : {
    "content" : """השם 'יהדות' נגזר משמם של היהודים, תושבי ממלכת יהודה (שתחת השלטון הרומאי נקראה פרובינקיה יודאיה), ששמה נגזר משמו של שבט יהודה, שנקרא על שמו של יהודה בנו של יעקב. בספרות חז"ל נמצא ביטוי הקדום במקורו: "דת משה ויהודים"[11] אשר מובנו מצומצם[12]. ואולם המונח "יהדות" במובנו הרחב, כמתאר את מכלול עולמו והווייתו של האדם היהודי, אינו מצוי בדברי חז"ל, והוא נדיר מאוד בספרות התורנית שלפני העת החדשה[13][14] מונח זה מופיע בשפה היוונית (‎᾿Ιουδαϊσμός; "יודאיסמוס"[15]) בספרות היהודית-ההלניסטית, לראשונה בספר מקבים ב,[16][13] (כמו גם המונח "הלניסטיים" ככינוי ליהודים המאמצים זהות יוונית המופיע אף הוא לראשונה בחיבור זה)[17]. המונח מופיע לאחר מכן גם בספר מקבים ד[18], בברית החדשה[19] ובכתובות אפיגרפיות[20] נראה שהראשון שהשתמש במונח באופן שיטתי (קודם היה נדיר מאוד ובהקשר שאינו חד־משמעי) היה אב הכנסייה טרטוליאנוס, בראשית המאה השלישית. הוא עשה זאת כמעין שם גנאי, מאחר שנזקק לתואר להגדיר בו את היהודים לאחר שנדחו, לשיטתו, מעם ישראל הנבחר שהמשיך בכנסייה, והוסיפו להתקיים כמעין "קליפה מנוונת" ללא מקדש וקרבנות, במצב של "מרד נגד האל"[21].

במאות ה-18 וה-19 הפך המונח "יהדות" לשכיח בפי יהודים, בהשאלה מגרמנית. מייסדי "חכמת ישראל" כינו את דתם וזהותם בתור Judenthum (יודנטום), והביטוי תורגם לעברית וליידיש במזרח אירופה. המילה נעשתה רווחת בקרב כל החוגים[22], כשהיא מחליפה מונחים כמו "עם ישראל" ו"תורה". התלמוד מביא הגדרה לשם "יהודי" - כל הכופר בעבודה זרה נקרא יהודי, ומביא הוכחה לטענתו מכך שכתוב לגבי מרדכי "איש יהודי היה בשושן הבירה", ובסופו של אותו פסוק הוא נקרא "איש ימיני". מכיוון שמרדכי היה משבט בנימין, הוא נקרא יהודי כי הוא כפר בעבודה זרה ולא השתחווה להמן.""",
    "language" : "Hebrew",
    "glossary" : """יהדות: מכלול עולמו והווייתו של האדם היהודי, הכולל את הדת, התרבות, והזהות היהודית.
יהודים: בני העם היהודי, תושבי ממלכת יהודה, שמם נגזר משבט יהודה.
ממלכת יהודה: ממלכה קדומה בארץ ישראל, שממנה נגזר שמם של היהודים.
פרובינקיה יודאיה: השם הרומאי לממלכת יהודה תחת שלטון האימפריה הרומית.
שבט יהודה: אחד משנים-עשר שבטי ישראל, שממנו נגזר שמה של ממלכת יהודה.
יהודה בן יעקב: אחד מבניו של יעקב אבינו, שעל שמו נקרא שבט יהודה.
חז"ל: חכמינו זכרונם לברכה, חכמי התורה שבעל פה שפעלו בתקופת המשנה והתלמוד.
דת משה ויהודים: ביטוי קדום המתאר את הדת היהודית כפי שמופיעה בספרות חז"ל.
ספרות תורנית: כתבים יהודיים העוסקים בתורה ובפרשנותה, בעיקר לפני העת החדשה.
העת החדשה: תקופה היסטורית שהחלה במאות ה-18 וה-19, שבה השתנה השימוש במונח "יהדות".
יודאיסמוס: המונח היווני ליהדות, שהופיע לראשונה בספרות היהודית-ההלניסטית.
ספר מקבים ב: ספר יהודי-היסטורי מהתקופה ההלניסטית, שבו מופיע לראשונה המונח "יודאיסמוס".
הלניסטיים: יהודים שאימצו זהות יוונית בתקופה ההלניסטית, כפי שמוזכר בספר מקבים ב.
ספר מקבים ד: ספר יהודי נוסף מהתקופה ההלניסטית שבו מופיע המונח "יודאיסמוס".
הברית החדשה: כתבי הקודש של הנצרות, שבהם מופיע המונח "יודאיסמוס".
כתובות אפיגרפיות: כתובות עתיקות שנחרטו על גבי אבנים או חומרים אחרים, שבהן מופיע המונח "יודאיסמוס".
טרטוליאנוס: אב כנסייה נוצרי מהמאה השלישית, שהשתמש במונח "יהדות" באופן שיטתי.
חכמת ישראל: תנועה יהודית מהמאה ה-19 שהתמקדה בחקר התרבות וההיסטוריה היהודית.
Judenthum: המונח הגרמני ליהדות, ששימש את מייסדי חכמת ישראל ותורגם לעברית וליידיש.
עם ישראל: כינוי לעם היהודי, ששימש לתיאור הזהות היהודית לפני שהמונח "יהדות" נעשה רווח.
תורה: כתבי הקודש היהודיים הכוללים את חמשת חומשי התורה, וכן את הפרשנות והמסורת היהודית.
תלמוד: אוסף כתבים יהודיים הכולל את המשנה והגמרא, ומהווה את הבסיס לתורה שבעל פה.
מרדכי: דמות מקראית ממגילת אסתר, שנקרא יהודי בשל סירובו להשתחוות להמן.
שושן הבירה: עיר מרכזית בממלכת פרס שבה התרחשו אירועי מגילת אסתר.
המן: דמות מקראית ממגילת אסתר, אויב היהודים שניסה להשמידם.
שבט בנימין: אחד משנים-עשר שבטי ישראל, שממנו הגיע מרדכי.
עבודה זרה: פולחן לאלים אחרים, שממנו נמנעו היהודים כחלק מזהותם הדתית.""",
    "bad_questions" : []},
    
    # 2) Supervised learning
    "Supervised_learning": {
    "content" : """Supervised learning algorithms build a mathematical model of a set of data that contains both the inputs and the desired outputs.[48] The data, known as training data, consists of a set of training examples. Each training example has one or more inputs and the desired output, also known as a supervisory signal. In the mathematical model, each training example is represented by an array or vector, sometimes called a feature vector, and the training data is represented by a matrix. Through iterative optimisation of an objective function, supervised learning algorithms learn a function that can be used to predict the output associated with new inputs.[49] An optimal function allows the algorithm to correctly determine the output for inputs that were not a part of the training data. An algorithm that improves the accuracy of its outputs or predictions over time is said to have learned to perform that task""",
    "language" : "English",
    "glossary" : """Supervised learning algorithms: Algorithms that build a mathematical model using data containing both inputs and desired outputs to predict outcomes for new inputs.
Mathematical model: A representation of data and relationships between variables using mathematical expressions or structures.
Training data: A dataset consisting of inputs and corresponding desired outputs used to train supervised learning algorithms.
Training examples: Individual data points within the training data, each containing inputs and their associated desired output.
Inputs: Variables or features provided to a model to make predictions or perform computations.
Desired outputs: The target results or labels that a supervised learning algorithm aims to predict.
Supervisory signal: The desired output provided to guide the learning process in supervised learning algorithms.
Array: A structured collection of elements, often numbers, arranged in rows and columns.
Vector: A one-dimensional array representing a sequence of values, often used to describe features of a training example.
Feature vector: A vector containing numerical representations of the features of a training example.
Matrix: A two-dimensional array used to represent training data, with rows corresponding to training examples and columns to features.
Iterative optimisation: A process of repeatedly adjusting parameters to improve the performance of a model based on an objective function.
Objective function: A mathematical expression that evaluates the performance of a model, guiding its optimisation.
Optimal function: The learned function that accurately predicts outputs for inputs, including those not in the training data.
Predictions: The outputs generated by a model based on given inputs, representing its inferred results.""",
    "bad_questions" : []},
    
    # 3) The Ottoman Empire on the Eve of World War I
    "The_Ottoman_Empire_on_the_Eve_of_World_War_I" : {
    "content" : """האימפריה העות'מאנית ערב מלחמת העולם הראשונה
אימוני הצבא העות'מאני לפני מלחמת העולם הראשונה נעשו בסיוע משלחת קציני צבא גרמניים. אימוני הצי לעומת זאת נעשו בסיוע משלחת קציני צי בריטיים. לכן תמך הצבא בברית עם גרמניה והצי תמך בברית עם בריטניה. האימפריה העות'מאנית רכשה מבריטניה כ-40 אוניות מלחמה. גולת הכותרת היה רכש שתי אוניות מערכה גדולות מסוג סוּפֶּר-דרֶדנוּט, סולטאן עות'מאן הראשון ורשאדייה במספנה בריטית. לכל אחת מהן היה דחי של כ-30000 טון והיא נשאה 10 תותחים בקוטר 343 מ"מ. עבור שתי אוניות אלו שילמו העות'מאנים סכום עצום (בערכים של אז) בסך שבעה וחצי מיליון לירות שטרלינג שגויסו מהציבור הטורקי במגבית עממית, לאומית ודתית.

ב-1 באוגוסט 1914 הכריזה גרמניה מלחמה על רוסיה, והגישה לצרפת אולטימטום לפני שתכריז עליה מלחמה. ב-2 באוגוסט בעת ששתי האניות עמדו להימסר לצוותים טורקיים שכבר שהו בבריטניה, הודיע שר הימייה הבריטי צ'רצ'יל על הפקעת האוניות, משום סכנת המלחמה וצורך לאומי בריטי. הפיצוי שהובטח לטורקיה היה קטן, ורק בתנאי שתשמור על נייטרליות במלחמה. הפקעת האניות עוררה זעם רב בציבור, בצי ובממשל הטורקי, והחלישה את התנגדות הצי הטורקי לברית עם גרמניה.

ביולי 1914, כמה שבועות לפני פרוץ המלחמה והפקעת האניות אך אחרי רצח פרנץ פרדיננד בסרייבו, הציע שר המלחמה העות'מאני הפרו גרמני, אֶנווֶר פאשה, לגרמניה, לכרות ברית סודית לסיוע הדדי בלתי מותנה בעת מלחמה. גרמניה לא מיהרה להשיב בחיוב, ורק ב-1 באוגוסט, אחרי שהכריזה מלחמה על רוסיה והגישה אולטימטום לצרפת, חתמה גרמניה והחזירה את חוזה הברית לאִשרור טורקי. החוזה נחתם על ידי ממשלת טורקיה ב-2 באוגוסט, אך הממשלה העות'מאנית לא קיימה את מחויבותה לפי החוזה והעדיפה להישאר נייטרלית, בטענה נכונה שהחוזה לא אושר סופית בהיעדר חתימת הסוּלטן. כתוצאה מכך, לא הכריזה האימפריה העות'מאנית מלחמה על רוסיה ולא חסמה את מצרי הבוספורוס והדרדנלים לשיט רוסי. תוך יומיים הוכרזו מצבי מלחמה גם בין גרמניה לצרפת ובריטניה, אך האימפריה העות'מאנית לא הצטרפה למלחמה.""",
    "language" : "Hebrew",
    "glossary" : """האימפריה העות'מאנית: ישות מדינית שהתקיימה בין השנים 1299–1923 ושלטה על שטחים נרחבים באירופה, אסיה ואפריקה.
מלחמת העולם הראשונה: עימות גלובלי שהתרחש בין השנים 1914–1918, בו היו מעורבות מדינות רבות משני צידי המתרס.
הצבא העות'מאני: הכוח הצבאי של האימפריה העות'מאנית, אשר פעל להגנתה ולהרחבת שטחיה.
משלחת קציני צבא גרמניים: צוות קצינים גרמניים שסייעו באימוני הצבא העות'מאני ערב מלחמת העולם הראשונה.
משלחת קציני צי בריטיים: צוות קצינים בריטיים שסייעו באימוני הצי העות'מאני ערב מלחמת העולם הראשונה.
הצי העות'מאני: הכוח הימי של האימפריה העות'מאנית, אשר היה אחראי על הגנת גבולותיה הימיים.
ברית עם גרמניה: הסכם שיתוף פעולה צבאי בין האימפריה העות'מאנית לגרמניה ערב מלחמת העולם הראשונה.
ברית עם בריטניה: הסכם שיתוף פעולה צבאי בין האימפריה העות'מאנית לבריטניה ערב מלחמת העולם הראשונה.
אוניות מלחמה: כלי שיט גדולים ומחומשים שנועדו ללחימה ימית.
סוּפֶּר-דרֶדנוּט: סוג מתקדם של אוניות מערכה בעלות חימוש כבד ויכולת לחימה גבוהה.
סולטאן עות'מאן הראשון: אחת משתי אוניות מערכה גדולות שנרכשו על ידי האימפריה העות'מאנית מבריטניה.
רשאדייה: אוניית מערכה גדולה שנרכשה על ידי האימפריה העות'מאנית מבריטניה.
דחי: משקל כולל של כלי שיט, כולל מטען, צוות ודלק.
תותחים בקוטר 343 מ"מ: חימוש כבד שנשאו אוניות המלחמה מסוג סוּפֶּר-דרֶדנוּט.
לירות שטרלינג: מטבע בריטי ששימש לתשלום עבור אוניות המלחמה שנרכשו על ידי האימפריה העות'מאנית.
מגבית עממית, לאומית ודתית: גיוס כספים מהציבור הטורקי למימון רכישת אוניות המלחמה.
שר הימייה הבריטי: תפקיד ממשלתי בבריטניה האחראי על ענייני הצי והימייה.
צ'רצ'יל: וינסטון צ'רצ'יל, שר הימייה הבריטי בזמן מלחמת העולם הראשונה.
הפקעת האוניות: פעולה של החרמת אוניות המלחמה העות'מאניות על ידי בריטניה ערב מלחמת העולם הראשונה.
שר המלחמה העות'מאני: תפקיד ממשלתי באימפריה העות'מאנית האחראי על ענייני הצבא והמלחמה.
אֶנווֶר פאשה: שר המלחמה העות'מאני שתמך בברית עם גרמניה ערב מלחמת העולם הראשונה.
ברית סודית לסיוע הדדי: הסכם חשאי בין האימפריה העות'מאנית לגרמניה לסיוע צבאי בעת מלחמה.
מצרי הבוספורוס: נתיב מים המחבר בין הים השחור לים המרמרה, בעל חשיבות אסטרטגית.
מצרי הדרדנלים: נתיב מים המחבר בין ים המרמרה לים האגאי, בעל חשיבות אסטרטגית.
שיט רוסי: תנועת כלי שיט רוסיים דרך מצרי הבוספורוס והדרדנלים.""",
    "bad_questions" : []},
    
    # 4) Macroeconomics Outout and income
    "Macroeconomics_Outout_and_income" : {
    "content" : """National output is the total amount of everything a country produces in a given period of time. Everything that is produced and sold generates an equal amount of income. The total net output of the economy is usually measured as gross domestic product (GDP). Adding net factor incomes from abroad to GDP produces gross national income (GNI), which measures total income of all residents in the economy. In most countries, the difference between GDP and GNI are modest so that GDP can approximately be treated as total income of all the inhabitants as well, but in some countries, e.g. countries with very large net foreign assets (or debt), the difference may be considerable.""",
    "language" : "English",
    "glossary" : """National output: The total amount of everything a country produces in a given period of time.
Gross domestic product (GDP): The total net output of the economy, measuring the value of all goods and services produced within a country's borders during a specific time period.
Net factor incomes from abroad: The difference between income earned by residents from foreign investments and income earned by foreign residents from domestic investments.
Gross national income (GNI): The total income of all residents in an economy, calculated by adding net factor incomes from abroad to gross domestic product (GDP).
Total net output: The overall production of goods and services in an economy, typically measured as GDP.
Income: The monetary gain generated from the production and sale of goods and services.
Net foreign assets: The difference between a country's foreign assets and its foreign liabilities.
Debt: The amount of money borrowed by a country or entity that must be repaid, often with interest.""",
    "bad_questions" : []},
    }

ONE_SHOT_MCQ_CREATION_PAIRS = [
    {"user": PromptBuilder().create_question_prompt(
        article_content=ARTICALES["Origin_of_the_name_Judaism"]["content"],
        chain_of_thought=True,
        lang=ARTICALES["Origin_of_the_name_Judaism"]["language"],
        bad_questions=ARTICALES["Origin_of_the_name_Judaism"]["bad_questions"],
        glossary=ARTICALES["Origin_of_the_name_Judaism"]["glossary"]
    ),
    "assistant": """**A) הנימוק לשאלה ולמה היא בוחנת הבנה של המאמר:**
השאלה בוחנת את ההבנה של התפתחות המונח "יהדות" מבחינה היסטורית, לשונית ותרבותית, כפי שמתואר במאמר. היא דורשת מהמשיב לזכור ולהבין את המקורות השונים שבהם הופיע המונח, את ההקשר שבו נעשה בו שימוש לאורך הדורות, ואת שינויי המשמעות והזהות היהודית הקשורים בו. שאלה כזו בוחנת גם ידע על מקורות טקסטואליים חשובים (כגון חז"ל, ספר מקבים, הברית החדשה) וגם את הבנת התהליכים התרבותיים והלשוניים של יהדות אירופה במאות האחרונות.

---

**ב) שאלה רב-ברירה עם חמש אפשרויות:**

מהי ההתפתחות ההיסטורית של השימוש במונח "יהדות"?

א) המונח "יהדות" הופיע לראשונה בספרות חז"ל, ותמיד שימש לתיאור דת ישראל במובנה הרחב.
ב) המונח "יהדות" נוצר בתקופת התנ"ך, והשתמר ללא שינוי לאורך כל ההיסטוריה היהודית.
ג) המונח "יהדות" הופיע לראשונה בשפה היוונית בספרות היהודית-ההלניסטית, הוזכר בספר מקבים ב, ולאחר מכן אומץ בהרחבה במאות ה-18 וה-19, בעיקר בהשפעת השפה הגרמנית ותנועת "חכמת ישראל".
ד) השימוש הראשון במונח "יהדות" נעשה על ידי חז"ל במובן של כופר בעבודה זרה, והוא נותר בעל משמעות שלילית עד העת החדשה.
ה) טרטוליאנוס טבע את המונח "יהדות" במאה ה-20 במסגרת פולמוס נוצרי-יהודי, והמילה הפכה לשם גנאי ליהודים רק בתקופה זו.

✔️ **תשובה נכונה: ג**
""", "language": ARTICALES["Origin_of_the_name_Judaism"]["language"]},
    {"user": PromptBuilder().create_question_prompt(
        article_content=ARTICALES["Supervised_learning"]["content"],
        chain_of_thought=True,
        lang=ARTICALES["Supervised_learning"]["language"],
        bad_questions=ARTICALES["Supervised_learning"]["bad_questions"],
        glossary=ARTICALES["Supervised_learning"]["glossary"]
    ),
    "assistant": """**A) Reasoning behind the question:**

This question is designed to assess a deep understanding of how supervised learning works, based on the key concepts introduced in the article and glossary. It tests whether the person understands the role of training data, the structure of data representation (arrays, vectors, matrices), and the goal of finding an optimal function through iterative optimisation. By focusing on the *process* and *purpose* of supervised learning, the question ensures that the person isn’t just recognizing definitions but actually grasps how the concepts connect in practice.

---

**B) Full question with five alternatives:**

Which of the following best describes how a supervised learning algorithm uses training data to make accurate predictions for new, unseen inputs?

A) It organizes the inputs into separate categories using clustering techniques, then applies those categories to new inputs.

B) It analyzes the training data using reinforcement signals from external feedback to determine the most effective actions for prediction.

C) It builds a mathematical model using training examples—each represented as vectors or arrays—contained within a matrix, and through iterative optimisation of an objective function, learns an optimal function that maps inputs to desired outputs, allowing it to make accurate predictions on new inputs.

D) It creates a decision tree from unlabeled data by detecting hidden patterns, and then generalizes those patterns to predict future outcomes.

E) It memorizes the input-output pairs in the training data and selects the closest match when predicting new inputs.

**Correct answer:** C
""", "language": ARTICALES["Supervised_learning"]["language"]},
    {"user": PromptBuilder().create_question_prompt(
        article_content=ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["content"],
        chain_of_thought=True,
        lang=ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["language"],
        bad_questions=ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["bad_questions"],
        glossary=ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["glossary"]
    ),
    "assistant": """**A) נימוק לשאלה ולמה היא בודקת הבנה של המאמר:**

השאלה נועדה לבדוק את ההבנה של רצף האירועים והקשרים בין הצדדים המעורבים – האימפריה העות'מאנית, גרמניה ובריטניה – ערב פרוץ מלחמת העולם הראשונה. היא משלבת ידע על הדינמיקה הפנימית בין הצבא לצי באימפריה, העסקאות לרכישת אוניות מלחמה, וההשלכות של הפקעת האוניות מצד בריטניה. שאלת רב-ברירה זו אינה מסתמכת על זיכרון פרטים בודדים בלבד, אלא דורשת הבנה כוללת של המניעים, ההתרחשויות וההשפעות המדיניות.

---

**B) השאלה:**

מה מהבאים מתאר בצורה הנכונה והשלמה ביותר את השתלשלות האירועים והעמדות של האימפריה העות'מאנית ערב כניסתה האפשרית למלחמת העולם הראשונה?

א) האימפריה העות'מאנית תמכה באופן גורף בברית עם בריטניה, רכשה ממנה אוניות מלחמה, וקיבלה אותן בהצלחה למרות המצב הביטחוני המתוח.

ב) בעקבות הכרזת גרמניה מלחמה על רוסיה, האימפריה העות'מאנית הכריזה מיד על מלחמה גם היא, והפעילה את אוניות המלחמה שרכשה מבריטניה כנגד הצי הרוסי.

ג) הפקעת אוניות המלחמה שרכשה האימפריה העות'מאנית מבריטניה על ידי צ'רצ'יל גרמה לזעם רב בטורקיה, החלישה את ההתנגדות לברית עם גרמניה, אך למרות חתימת ברית סודית עם גרמניה, לא הצטרפה האימפריה מיד למלחמה בטענה שהחוזה לא אושר על ידי הסולטאן.

ד) האימפריה העות'מאנית הכריזה על נייטרליות מלאה ונמנעה מלבצע כל מגעים מדיניים עם גרמניה או בריטניה, למרות ניסיונות חוזרים לשכנעה להצטרף לברית צבאית.

ה) אֶנווֶר פאשה, שר הימייה העות'מאני, ניהל לבדו את כל המגעים עם גרמניה, קיבל את האוניות מבריטניה, וחתם על חוזה ברית שהופעל מידית ללא צורך באישור נוסף.

**תשובה נכונה:** ג)
""", "language": ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["language"]},
    {"user": PromptBuilder().create_question_prompt(
        article_content=ARTICALES["Macroeconomics_Outout_and_income"]["content"],
        chain_of_thought=True,
        lang=ARTICALES["Macroeconomics_Outout_and_income"]["language"],
        bad_questions=ARTICALES["Macroeconomics_Outout_and_income"]["bad_questions"],
        glossary=ARTICALES["Macroeconomics_Outout_and_income"]["glossary"]
    ),
    "assistant": """**A) Reasoning behind the question, and why it assesses understanding of the article:**

This question is designed to assess a solid understanding of how key economic indicators—such as GDP, GNI, and national output—are defined and interrelated. It also checks whether the person can distinguish between concepts like domestic production and income earned from international investments. Understanding these relationships is essential for interpreting economic performance at the national level. The question integrates multiple terms from the glossary to test comprehension beyond memorization.

---

**B) Full question with five alternatives:**

Which of the following statements best describes the relationship between gross domestic product (GDP), gross national income (GNI), and national output?

A) GDP measures the total value of foreign investments held by a country, while GNI excludes any income from abroad.

B) National output refers only to services produced within a country, and is not included in GDP or GNI.

C) National output is the total production in a country, usually measured by GDP; GNI is calculated by adding net factor incomes from abroad to GDP, representing total income of all residents.

D) GNI is always equal to GDP because foreign income has no impact on a country's total income.

E) GDP includes both domestic and international production, while GNI measures only what is produced within national borders.

**Correct answer:** C
""", "language": ARTICALES["Macroeconomics_Outout_and_income"]["language"]}
]

ONE_SHOT_MCQ_CONVERSION_TO_JSON_PAIRS = [
    {"user": PromptBuilder().convert_question_to_json_prompt(ONE_SHOT_MCQ_CREATION_PAIRS[0]["assistant"]),
    "assistant": """{
"question": "מהי ההתפתחות ההיסטורית של השימוש במונח "יהדות"?",
"options": {
"A": "המונח "יהדות" הופיע לראשונה בספרות חז"ל, ותמיד שימש לתיאור דת ישראל במובנה הרחב.",
"B": "המונח "יהדות" נוצר בתקופת התנ"ך, והשתמר ללא שינוי לאורך כל ההיסטוריה היהודית.",
"C": "המונח "יהדות" הופיע לראשונה בשפה היוונית בספרות היהודית-ההלניסטית, הוזכר בספר מקבים ב, ולאחר מכן אומץ בהרחבה במאות ה-18 וה-19, בעיקר בהשפעת השפה הגרמנית ותנועת "חכמת ישראל".",
"D": "השימוש הראשון במונח "יהדות" נעשה על ידי חז"ל במובן של כופר בעבודה זרה, והוא נותר בעל משמעות שלילית עד העת החדשה.",
"E": "טרטוליאנוס טבע את המונח "יהדות" במאה ה-20 במסגרת פולמוס נוצרי-יהודי, והמילה הפכה לשם גנאי ליהודים רק בתקופה זו."
},
"correct_answer": "C"
}
""", "language": ARTICALES["Origin_of_the_name_Judaism"]["language"]},
    {"user": PromptBuilder().convert_question_to_json_prompt(ONE_SHOT_MCQ_CREATION_PAIRS[1]["assistant"]),
    "assistant": """{
"question": "Which of the following best describes how a supervised learning algorithm uses training data to make accurate predictions for new, unseen inputs?",
"options": {
"A": "It organizes the inputs into separate categories using clustering techniques, then applies those categories to new inputs.",
"B": "It analyzes the training data using reinforcement signals from external feedback to determine the most effective actions for prediction.",
"C": "It builds a mathematical model using training examples—each represented as vectors or arrays—contained within a matrix, and through iterative optimisation of an objective function, learns an optimal function that maps inputs to desired outputs, allowing it to make accurate predictions on new inputs.",
"D": "It creates a decision tree from unlabeled data by detecting hidden patterns, and then generalizes those patterns to predict future outcomes.",
"E": "It memorizes the input-output pairs in the training data and selects the closest match when predicting new inputs."
},
"correct_answer": "C"
}
""", "language": ARTICALES["Supervised_learning"]["language"]},
    {"user": PromptBuilder().convert_question_to_json_prompt(ONE_SHOT_MCQ_CREATION_PAIRS[2]["assistant"]),
    "assistant": """{
"question": "מה מהבאים מתאר בצורה הנכונה והשלמה ביותר את השתלשלות האירועים והעמדות של האימפריה העות'מאנית ערב כניסתה האפשרית למלחמת העולם הראשונה?",
"options": {
"A": "האימפריה העות'מאנית תמכה באופן גורף בברית עם בריטניה, רכשה ממנה אוניות מלחמה, וקיבלה אותן בהצלחה למרות המצב הביטחוני המתוח.",
"B": "בעקבות הכרזת גרמניה מלחמה על רוסיה, האימפריה העות'מאנית הכריזה מיד על מלחמה גם היא, והפעילה את אוניות המלחמה שרכשה מבריטניה כנגד הצי הרוסי.",
"C": "הפקעת אוניות המלחמה שרכשה האימפריה העות'מאנית מבריטניה על ידי צ'רצ'יל גרמה לזעם רב בטורקיה, החלישה את ההתנגדות לברית עם גרמניה, אך למרות חתימת ברית סודית עם גרמניה, לא הצטרפה האימפריה מיד למלחמה בטענה שהחוזה לא אושר על ידי הסולטאן.",
"D": "האימפריה העות'מאנית הכריזה על נייטרליות מלאה ונמנעה מלבצע כל מגעים מדיניים עם גרמניה או בריטניה, למרות ניסיונות חוזרים לשכנעה להצטרף לברית צבאית.",
"E": "אֶנווֶר פאשה, שר הימייה העות'מאני, ניהל לבדו את כל המגעים עם גרמניה, קיבל את האוניות מבריטניה, וחתם על חוזה ברית שהופעל מידית ללא צורך באישור נוסף."
},
"correct_answer": "C"
}
""", "language": ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["language"]},
    {"user": PromptBuilder().convert_question_to_json_prompt(ONE_SHOT_MCQ_CREATION_PAIRS[3]["assistant"]),
    "assistant": """{
"question": "Which of the following statements best describes the relationship between gross domestic product (GDP), gross national income (GNI), and national output?",
"options": {
"A": "GDP measures the total value of foreign investments held by a country, while GNI excludes any income from abroad.",
"B": "National output refers only to services produced within a country, and is not included in GDP or GNI.",
"C": "National output is the total production in a country, usually measured by GDP; GNI is calculated by adding net factor incomes from abroad to GDP, representing total income of all residents.",
"D": "GNI is always equal to GDP because foreign income has no impact on a country's total income.",
"E": "GDP includes both domestic and international production, while GNI measures only what is produced within national borders."
},
"correct_answer": "C"
}""", "language": ARTICALES["Macroeconomics_Outout_and_income"]["language"]}
]


ONE_SHOT_MCQ_LIST_ERRORS_PAIRS = [
    {"user": PromptBuilder().list_question_errors_prompt(article_content=ARTICALES["Origin_of_the_name_Judaism"]["content"],
                                                         question_text="""{
"question": "מהי ההתפתחות ההיסטורית של השימוש במונח "יהדות"?",
"options": {
"A": "המונח "יהדות" הופיע לראשונה בספרות חז"ל, ותמיד שימש לתיאור דת ישראל במובנה הרחב.",
"B": "המונח "יהדות" נוצר בתקופת התנ"ך, והשתמר ללא שינוי לאורך כל ההיסטוריה היהודית.",
"C": "המונח "יהדות" הופיע לראשונה בשפה היוונית בספרות היהודית-ההלניסטית, הוזכר בספר מקבים ב, ולאחר מכן אומץ בהרחבה במאות ה-18 וה-19, בעיקר בהשפעת השפה הגרמנית ותנועת "חכמת ישראל".",
"D": "השימוש הראשון במונח "יהדות" נעשה על ידי חז"ל במובן של כופר בעבודה זרה, והוא נותר בעל משמעות שלילית עד העת החדשה.",
"E": "טרטוליאנוס טבע את המונח "יהדות" במאה ה-20 במסגרת פולמוס נוצרי-יהודי, והמילה הפכה לשם גנאי ליהודים רק בתקופה זו."
},
"correct_answer": "C"
}
""",
                                                         glossary=ARTICALES["Origin_of_the_name_Judaism"]["glossary"]),
    "assistant": """1. **Ambiguity in phrasing of correct option (C):** The phrase *"ולאחר מכן אומץ בהרחבה במאות ה-18 וה-19"* may imply an immediate and direct link between the ancient Greek use and the modern usage, without clarifying the significant historical gap and change in context. It could be misinterpreted as a continuous tradition.

2. **Overstatement in option C regarding "הוזכר בספר מקבים ב":** While the Greek term *"יודאיסמוס"* אכן מופיע בספר מקבים ב, חשוב לציין שהמונח העברי "יהדות" במובנו המודרני **לא** מופיע שם. לכן, הקישור הישיר בין המונח ההלניסטי ל"יהדות" בעברית עלול להטעות.

3. **Lack of clarity in the stem's scope:** The question asks על *"השימוש במונח 'יהדות'"* אך אינו מבהיר אם הכוונה היא למונח בעברית בלבד, או גם למקבילים בשפות אחרות כמו יוונית וגרמנית. ניסוח מדויק יותר היה יכול לציין: *"התפתחות השימוש במונח 'יהדות' ובמקבילותיו בלשונות שונות."*

4. **Punctuation and quotation marks inconsistency:** The repeated use of double quotation marks around the word "יהדות" in both the stem and options may make the question harder to read. Consider using single quotes in Hebrew contexts consistently (e.g., ’יהדות’).

""", "language": ARTICALES["Origin_of_the_name_Judaism"]["language"]},
    {"user": PromptBuilder().list_question_errors_prompt(article_content=ARTICALES["Supervised_learning"]["content"],
                                                         question_text="""{
  "question": "Which of these is the best way a supervized learning algorithm predicts accurate data using new training outputs from unseen labels?",
  "options": {
    "A": "It groups the input into several clusters using classification methods, then forces those clusters on future inputs.",
    "B": "It scans the testing data using punishment and rewards from the outputs to learn the least effective results.",
    "C": "It randomly builds math models using examples that are not connected, stored inside a table, and then skips optimization to instantly find the exact answer for all new inputs.",
    "D": "It grows a tree of decisions from data with no labels by guessing at relationships, and uses those guesses to always predict the right result.",
    "E": "It completely memorizes all the answers and never generalizes, just guesses the first match for any new problem."
  },
  "correct_answer": "C"
}""",
                                                         glossary=ARTICALES["Supervised_learning"]["glossary"]),
        "assistant": """1. **Incorrect "correct_answer" label**: Option C is labeled as correct, but it contradicts the article. It describes a process that involves randomness, lack of optimization, and no connection between examples, which does not align with how supervised learning works. Supervised learning relies on *iterative optimisation* and *connected examples* in the *training data*.

2. **Misleading phrasing in the question stem**: The question uses the phrase "new training outputs from unseen labels," which is confusing. In supervised learning, we predict **outputs** for **new inputs**, not the other way around. Also, "unseen labels" is vague and may mislead students into thinking the labels (outputs) are used to create the model after prediction.

3. **Terminological inaccuracy**: The term "supervized" in the question stem is a misspelling of "supervised." While minor, spelling mistakes in technical questions can affect clarity and credibility.

4. **Logical flaw in all answer choices**: None of the provided answer options accurately describe the supervised learning process as defined in the article. An ideal correct option should mention elements like **inputs**, **desired outputs**, **training data**, **optimization of an objective function**, and **prediction of new outputs**, which none of the current choices do.
""",
        "language": ARTICALES["Supervised_learning"]["language"]},
    {"user": PromptBuilder().list_question_errors_prompt(article_content=ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["content"],
                                                         question_text="""{
  "question": "מה מהבאים מתאר את ההשתלשלות של האירועים והעמדות של האימפריה העות'מאנית לפני שנכנסה אולי למלחמת העולם הראשונה בצורה הכי נכונה ושלימה?",
  "options": {
    "A": "האימפריה העות'מאנית תמכה בברית עם בריטניה בכל הכוח, קנתה ממנה אוניות מלחמה, והם הגיעו כמו שצריך אפילו שהמצב הביטחוני היה מתוח.",
    "B": "גרמניה הכריזה מלחמה על רוסיה, ואז האימפריה העות'מאנית ישר גם הכריזה מלחמה והשתמשה באוניות המלחמה שהיא קנתה מבריטניה נגד הצי של רוסיה.",
    "C": "צ׳רצ׳יל לקח את האוניות שהאימפריה קנתה מבריטניה וזה עשה הרבה כעס בטורקיה, ואז אנשים פחות התנגדו לברית עם גרמניה, אבל למרות שהיה חוזה סודי עם גרמניה, האימפריה לא נכנסה ישר למלחמה כי אמרו שהסולטן לא אישר את זה.",
    "D": "האימפריה העות'מאנית אמרה שהיא נייטרלית לגמרי ולא עשתה שום קשרים מדיניים עם גרמניה ועם בריטניה, אפילו שניסו הרבה פעמים לשכנע אותה להצטרף לברית צבאית.",
    "E": "אנור פאשה, שהיה שר של הים של האימפריה, הוא לבד ניהל הכל עם גרמניה, קיבל את האוניות מבריטניה וחתם על חוזה ברית שהתחיל לפעול ישר בלי אישורים."
  },
  "correct_answer": "C"
}""",
                                                         glossary=ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["glossary"]),
            "assistant": """1. **Minor inaccuracy in correct option (C):** האימפריה לא "אמרה שהסולטן לא אישר את זה" באופן הצהרתי, אלא נטען שהחוזה לא מחייב כי הסולטן לא חתם עליו – יש הבדל דק בין תירוץ רשמי לבין טענה פורמלית של אי-אישור.

2. **שימוש לא מדויק בתואר "שר של הים" באופציה E:** אנור פאשה היה שר המלחמה (היבשתי), לא שר הימייה. הניסוח הזה עלול לבלבל תלמידים שלא שמים לב להבדלים בין תפקידי שרים.

3. **אופציה A יוצרת רושם מטעה כאילו האוניות נמסרו בפועל:** היא מתעלמת לגמרי מהפקעת האוניות, שזה אירוע מרכזי בטקסט. ניסוח האופציה יוצר סתירה בולטת לעובדות הכתובות.

4. **שפה מעט עממית מדי באופציות (כמו "כמו שצריך", "הוא לבד ניהל הכל")** – ייתכן שהיא מתאימה לקהלים צעירים, אך עלולה לגרום לחוסר דיוק או חוסר בהירות בבחינה פורמלית.

5. **אין הבחנה ברורה בין עמדות הצבא והצי באופציות עצמן, למרות שזה נושא חשוב בטקסט.** אף אופציה לא מדגישה את הפיצול בין התמיכה בגרמניה לבין התמיכה בבריטניה, פרטית שהופיעה בתחילת המאמר. זו החמצה בתכנון ההסחות (distractors).
""",    "language": ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["language"]},
    {"user": PromptBuilder().list_question_errors_prompt(article_content=ARTICALES["Macroeconomics_Outout_and_income"]["content"],
                                                         question_text="""{
"question": "Which of the following statements best describes the relationship between gross domestic product (GDP), gross national income (GNI), and national output?",
"options": {
"A": "GDP measures the total value of foreign investments held by a country, while GNI excludes any income from abroad.",
"B": "National output refers only to services produced within a country, and is not included in GDP or GNI.",
"C": "National output is the total production in a country, usually measured by GDP; GNI is calculated by adding net factor incomes from abroad to GDP, representing total income of all residents.",
"D": "GNI is always equal to GDP because foreign income has no impact on a country's total income.",
"E": "GDP includes both domestic and international production, while GNI measures only what is produced within national borders."
},
"correct_answer": "C"
}""",
                                                         glossary=ARTICALES["Macroeconomics_Outout_and_income"]["glossary"]),
     "assistant": """No errors found.""",
     "language": ARTICALES["Macroeconomics_Outout_and_income"]["language"]}
]

#improve_question_prompt
ONE_SHOT_MCQ_IMPROVE_PAIRS = [
    {"user": PromptBuilder().improve_question_prompt(
        article_content=ARTICALES["Origin_of_the_name_Judaism"]["content"],
        question_text="""{
"question": "מהי ההתפתחות ההיסטורית של השימוש במונח "יהדות"?",
"options": {
"A": "המונח "יהדות" הופיע לראשונה בספרות חז"ל, ותמיד שימש לתיאור דת ישראל במובנה הרחב.",
"B": "המונח "יהדות" נוצר בתקופת התנ"ך, והשתמר ללא שינוי לאורך כל ההיסטוריה היהודית.",
"C": "המונח "יהדות" הופיע לראשונה בשפה היוונית בספרות היהודית-ההלניסטית, הוזכר בספר מקבים ב, ולאחר מכן אומץ בהרחבה במאות ה-18 וה-19, בעיקר בהשפעת השפה הגרמנית ותנועת "חכמת ישראל".",
"D": "השימוש הראשון במונח "יהדות" נעשה על ידי חז"ל במובן של כופר בעבודה זרה, והוא נותר בעל משמעות שלילית עד העת החדשה.",
"E": "טרטוליאנוס טבע את המונח "יהדות" במאה ה-20 במסגרת פולמוס נוצרי-יהודי, והמילה הפכה לשם גנאי ליהודים רק בתקופה זו."
},
"correct_answer": "C"
}
""",
        critique_text=ONE_SHOT_MCQ_LIST_ERRORS_PAIRS[0]["assistant"],
        glossary=ARTICALES["Origin_of_the_name_Judaism"]["glossary"]),
    "assistant": """{
"question": "כיצד התפתח השימוש ההיסטורי במונח 'יהדות' ובמקבילותיו בשפות אחרות לאורך הדורות?",
"options": {
"A": "המונח 'יהדות' הופיע לראשונה בספרות חז"ל, ותמיד שימש לתיאור דת ישראל במובנה הרחב.",
"B": "המונח 'יהדות' נוצר בתקופת התנ"ך, והשתמר ללא שינוי לאורך כל ההיסטוריה היהודית.",
"C": "המונח היווני 'יודאיסמוס' הופיע לראשונה בספר מקבים ב בתקופה ההלניסטית, ובהמשך, במאות ה-18 וה-19, התפתח השימוש במילה 'יהדות' בעברית, בהשפעת הגרמנית ותנועת 'חכמת ישראל'.",
"D": "השימוש הראשון במונח 'יהדות' נעשה על ידי חז"ל במובן של כופר בעבודה זרה, והוא נותר בעל משמעות שלילית עד העת החדשה.",
"E": "טרטוליאנוס טבע את המונח 'יהדות' במאה ה-20 במסגרת פולמוס נוצרי-יהודי, והמילה הפכה לשם גנאי ליהודים רק בתקופה זו."
},
"correct_answer": "C"
}
""", "language": ARTICALES["Origin_of_the_name_Judaism"]["language"]},
    {"user": PromptBuilder().improve_question_prompt(
        article_content=ARTICALES["Supervised_learning"]["content"],
        question_text="""{
  "question": "Which of the following best describes how a supervised learning algorithm uses training data to make accurate predictions for new, unseen inputs?",
  "options": {
    "A": "It organizes the inputs into separate categories using clustering techniques, then applies those categories to new inputs.",
    "B": "It analyzes the training data using reinforcement signals from external feedback to determine the most effective actions for prediction.",
    "C": "It builds a mathematical model using training examples—each represented as vectors or arrays—contained within a matrix, and without any optimization, memorizes the examples to make predictions on new inputs.",
    "D": "It creates a decision tree from unlabeled data by detecting hidden patterns, and then generalizes those patterns to predict future outcomes.",
    "E": "It memorizes the input-output pairs in the training data and selects the closest match when predicting new inputs."
  },
  "correct_answer": "C"
}""",
        critique_text="""1. **Incorrect Description in Correct Answer (Option C):** Option C, which is marked as the correct answer, contains a flawed statement: *“without any optimization, memorizes the examples to make predictions on new inputs.”* This contradicts the core concept of supervised learning, which involves optimizing a model to generalize beyond memorization. Including this error in the correct answer undermines the validity of the question.

2. **Inconsistent Terminology Across Options:** Some options (like A and D) use terminology such as “clustering” and “unlabeled data,” which are associated with unsupervised learning. While this is acceptable as a distractor, the use of “unlabeled data” in option D could confuse students if not clearly framed as incorrect within the context of supervised learning. Slightly rewording could make this clearer.

3. **Redundancy in Distractor E and Incorrect "Correct" Answer:** Option E mentions “memorizes the input-output pairs,” which is quite similar in concept to the error-laden “memorizes the examples” in option C. This may create confusion between the correct and incorrect options due to overlapping language.
""",
        glossary=ARTICALES["Supervised_learning"]["glossary"]),
    "assistant": """{
"question": "Which of the following best describes how a supervised learning algorithm uses training data to make accurate predictions for new, unseen inputs?",
"options": {
"A": "It groups inputs using clustering techniques and uses those groups to predict outcomes for new data.",
"B": "It uses feedback from external rewards or punishments to choose the best predictions over time.",
"C": "It builds a mathematical model using training examples—each represented as vectors or arrays—organized in a matrix, and through iterative optimisation of an objective function, learns a function that predicts outputs for new inputs.",
"D": "It finds patterns in unlabeled data using a decision tree and applies those patterns to make predictions.",
"E": "It memorizes the input-output pairs in the training data and selects the closest match when given a new input."
},
"correct_answer": "C"
}
""","language": ARTICALES["Supervised_learning"]["language"]},
    {"user": PromptBuilder().improve_question_prompt(
        article_content=ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["content"],
        question_text="""{
  "question": "מה מהבאים מתאר את ההשתלשלות של האירועים והעמדות של האימפריה העות'מאנית לפני שנכנסה אולי למלחמת העולם הראשונה בצורה הכי נכונה ושלימה?",
  "options": {
    "A": "האימפריה העות'מאנית תמכה בברית עם בריטניה בכל הכוח, קנתה ממנה אוניות מלחמה, והם הגיעו כמו שצריך אפילו שהמצב הביטחוני היה מתוח.",
    "B": "גרמניה הכריזה מלחמה על רוסיה, ואז האימפריה העות'מאנית ישר גם הכריזה מלחמה והשתמשה באוניות המלחמה שהיא קנתה מבריטניה נגד הצי של רוסיה.",
    "C": "צ׳רצ׳יל לקח את האוניות שהאימפריה קנתה מבריטניה וזה עשה הרבה כעס בטורקיה, ואז אנשים פחות התנגדו לברית עם גרמניה, אבל למרות שהיה חוזה סודי עם גרמניה, האימפריה לא נכנסה ישר למלחמה כי אמרו שהסולטן לא אישר את זה.",
    "D": "האימפריה העות'מאנית אמרה שהיא נייטרלית לגמרי ולא עשתה שום קשרים מדיניים עם גרמניה ועם בריטניה, אפילו שניסו הרבה פעמים לשכנע אותה להצטרף לברית צבאית.",
    "E": "אנור פאשה, שהיה שר של הים של האימפריה, הוא לבד ניהל הכל עם גרמניה, קיבל את האוניות מבריטניה וחתם על חוזה ברית שהתחיל לפעול ישר בלי אישורים."
  },
  "correct_answer": "C"
}""",
        critique_text=ONE_SHOT_MCQ_LIST_ERRORS_PAIRS[2]["assistant"],
        glossary=ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["glossary"]),
    "assistant": """{
"question": "איזו מהאפשרויות הבאות מתארת בצורה המדויקת והשלמה ביותר את ההשתלשלות של האירועים והעמדות של האימפריה העות'מאנית ערב כניסתה האפשרית למלחמת העולם הראשונה?",
"options": {
"A": "האימפריה העות'מאנית רכשה אוניות מבריטניה, קיבלה אותן בזמן, וחיזקה את הקשרים עם בריטניה על רקע תמיכת הצי בעמדה זו.",
"B": "גרמניה פתחה במלחמה, והאימפריה העות'מאנית מיד הצטרפה אליה, השתמשה באוניות שקיבלה מבריטניה ותקפה את רוסיה.",
"C": "בריטניה הפקיעה את האוניות שהעות'מאנים קנו, מה שעורר כעס ציבורי בטורקיה והחליש את ההתנגדות לברית עם גרמניה. נחתם חוזה סודי עם גרמניה, אך האימפריה לא הצטרפה מיד למלחמה בטענה שהסולטן לא אישר רשמית את ההסכם.",
"D": "האימפריה העות'מאנית שמרה על ניטרליות מוחלטת, לא יצרה קשרים עם אף צד, ודחתה כל ניסיון לשכנע אותה להצטרף לברית צבאית.",
"E": "אנוור פאשה, שהיה שר המלחמה, ניהל לבדו את המגעים עם גרמניה, קיבל את האוניות מבריטניה וחתם על ברית שהופעלה מידית וללא צורך באישור נוסף."
},
"correct_answer": "C"
}
""","language": ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["language"]},
    {"user": PromptBuilder().improve_question_prompt(
        article_content=ARTICALES["Macroeconomics_Outout_and_income"]["content"],
        question_text="""{
  "question": "Which sentence most best explain the relation of GDP, GNI and the national outbut?",
  "options": {
    "A": "GDP count all foreign investiments a country owns, and GNI don’t include any earning from other countries.",
    "B": "National output only talks about services done in one country, and it not part of GDP or GNI.",
    "C": "National output is what country buy from other countries; GNI is same as GDP but subtract taxes from it.",
    "D": "GNI always same as GDP because money from abroad never change the total income.",
    "E": "GDP has both inside and outside production, and GNI only measure what is made inside the borders."
  },
  "correct_answer": "C"
}
""",
        critique_text="""Incorrect correct answer key: Option C is labeled as correct, but it is factually incorrect. National output refers to the total value of goods and services produced in a country, not what is bought from other countries. GNI is not GDP minus taxes; it is GDP plus net income from abroad.

Confusing and grammatically incorrect language: Many options, including the question stem, contain poor grammar and awkward phrasing, making them hard to understand (e.g., "most best," "it not part," "don’t include any earning").

Misleading or incorrect content in options:

Option A wrongly states that GDP counts all foreign investments a country owns (it doesn’t—it includes domestic production).

Option D wrongly claims GNI is always the same as GDP.

Option E confuses the definitions—GDP includes domestic production; GNI includes domestic production plus net income from abroad.

Question stem is unclear: "Which sentence most best explain the relation..." is grammatically incorrect. It should be "Which sentence best explains the relationship among GDP, GNI, and national output?"

Terminology confusion: "National output" is not clearly defined in the context, which may confuse test-takers, especially since it's closely related to GDP.

No correct option provided: None of the options accurately describe the relationship between GDP, GNI, and national output.

Recommendation: The question should be rewritten with corrected grammar, clearer definitions, and at least one factually correct answer choice.""",
        glossary=ARTICALES["Macroeconomics_Outout_and_income"]["glossary"]),
    "assistant": """{
"question": "Which sentence best explains the relationship among GDP, GNI, and national output?",
"options": {
"A": "GDP measures the total production within a country, and GNI adds income earned from abroad to this total. National output usually refers to GDP.",
"B": "GNI only includes money sent by people living abroad, while GDP includes only imported goods. National output is the sum of both.",
"C": "National output means what people earn in other countries. GDP and GNI are not part of this calculation.",
"D": "GDP and GNI always measure the same thing because no income comes from abroad or goes out.",
"E": "GDP includes both local and foreign income, but GNI only includes income from within the country."
},
"correct_answer": "A"
}""","language": ARTICALES["Macroeconomics_Outout_and_income"]["language"]}
]

ONE_SHOT_ANSWER_MCQ_PAIRS = [
    {"user": PromptBuilder().answer_question_prompt(
        article_content=ARTICALES["Origin_of_the_name_Judaism"]["content"],
        question_text= ONE_SHOT_MCQ_IMPROVE_PAIRS[0]["assistant"][:-26]+"\n}",
        glossary=ARTICALES["Origin_of_the_name_Judaism"]["glossary"]),
     "assistant": "C",
     "language": ARTICALES["Origin_of_the_name_Judaism"]["language"]},
    {"user": PromptBuilder().answer_question_prompt(
        article_content=ARTICALES["Supervised_learning"]["content"],
        question_text= ONE_SHOT_MCQ_IMPROVE_PAIRS[1]["assistant"][:-26]+"\n}",
        glossary=ARTICALES["Supervised_learning"]["glossary"]),
     "assistant": "C",
     "language": ARTICALES["Supervised_learning"]["language"]},
    {"user": PromptBuilder().answer_question_prompt(
        article_content=ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["content"],
        question_text= ONE_SHOT_MCQ_IMPROVE_PAIRS[2]["assistant"][:-26]+"\n}",
        glossary=ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["glossary"]),
     "assistant": "C",
     "language": ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["language"]},
    {"user": PromptBuilder().answer_question_prompt(
        article_content=ARTICALES["Macroeconomics_Outout_and_income"]["content"],
        question_text= ONE_SHOT_MCQ_IMPROVE_PAIRS[3]["assistant"][:-26]+"\n}",
        glossary=ARTICALES["Macroeconomics_Outout_and_income"]["glossary"]),
     "assistant": "A",
     "language": ARTICALES["Macroeconomics_Outout_and_income"]["language"]},
]

ONE_SHOT_FIX_ANSWER_MCQ_PAIRS = [
    
]

ONE_SHOT_VALIDATE_LANGUAGE_PAIRS = [
    {"user": PromptBuilder().validate_language_prompt(
        question_text = ONE_SHOT_MCQ_IMPROVE_PAIRS[0]["assistant"],
        lang = ARTICALES["Origin_of_the_name_Judaism"]["language"]),
        "assistant": """Yes""",
        "language": ARTICALES["Origin_of_the_name_Judaism"]["language"]},
    {"user": PromptBuilder().validate_language_prompt(
        question_text = ONE_SHOT_MCQ_IMPROVE_PAIRS[1]["assistant"],
        lang = ARTICALES["Supervised_learning"]["language"]),
     "assistant": """Yes""",
     "language": ARTICALES["Supervised_learning"]["language"]},
    {"user": PromptBuilder().validate_language_prompt(
        question_text = """{
  "question": "Which of the following options most accurately and completely describes the sequence of events and the position of the Ottoman Empire just before it potentially entered World War I?",
  "options": {
    "A": "The Ottoman Empire bought ships from Britain, received them on time, and strengthened its ties with Britain, supported by the navy's position.",
    "B": "Germany started the war, and the Ottoman Empire immediately joined it, used the ships it got from Britain, and attacked Russia.",
    "C": "Britain took over the ships the Ottomans had bought, which caused public anger in Turkey and weakened resistance to an alliance with Germany. A secret agreement was signed with Germany, but the empire did not join the war right away, claiming the sultan had not officially approved the agreement.",
    "D": "The Ottoman Empire remained completely neutral, did not form ties with any side, and rejected all efforts to persuade it to join a military alliance.",
    "E": "Enver Pasha, who was the Minister of War, managed contacts with Germany on his own, received the ships from Britain, and signed an alliance that took effect immediately and did not require any further approval."
  },
  "correct_answer": "C"
}
""",
        lang =  ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["language"]),
     "assistant": """No""",
     "language": ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["language"]},
    {"user": PromptBuilder().validate_language_prompt(
        question_text = """{
  "question": "איזו מהמשפטים מסבירה בצורה הטובה ביותר את הקשר בין תוצר מקומי גולמי (תמ\"ג), הכנסה לאומית גולמית (תל\"ג), והתפוקה הלאומית?",
  "options": {
    "A": "תמ\"ג מודד את סך הייצור בתוך המדינה, ותל\"ג מוסיף לכך גם הכנסות שהתקבלו מחו\"ל. התפוקה הלאומית מתייחסת בדרך כלל לתמ\"ג.",
    "B": "תל\"ג כולל רק כסף שנשלח על ידי אנשים החיים בחו\"ל, בעוד שתמ\"ג כולל רק סחורות מיובאות. התפוקה הלאומית היא סכום של שניהם.",
    "C": "תפוקה לאומית פירושה מה שאנשים מרוויחים במדינות אחרות. תמ\"ג ותל\"ג אינם חלק מהחישוב הזה.",
    "D": "תמ\"ג ותל\"ג תמיד מודדים את אותו הדבר כי אין הכנסות שנכנסות מחו\"ל או יוצאות החוצה.",
    "E": "תמ\"ג כולל גם הכנסות מקומיות וגם מחו\"ל, אך תל\"ג כולל רק הכנסות מתוך המדינה."
  },
  "correct_answer": "A"
}
""",
        lang =  ARTICALES["Macroeconomics_Outout_and_income"]["language"]),
     "assistant": """No""",
     "language": ARTICALES["Macroeconomics_Outout_and_income"]["language"]}
]

ONE_SHOT_FIX_LANGUAGE_PAIRS = [
    {"user": PromptBuilder().fix_language_prompt(
        article_content = ARTICALES["Origin_of_the_name_Judaism"]["content"],
        question_text = """{
  "question": "How did the historical use of the term 'Judaism' and its equivalents in other languages develop over the ages?",
  "options": {
    "A": "The term 'Judaism' first appeared in rabbinic literature and was always used to describe the religion of Israel in its broad sense.",
    "B": "The term 'Judaism' was created during the Biblical period and remained unchanged throughout all of Jewish history.",
    "C": "The Greek term 'Ioudaismos' first appeared in the book of 2 Maccabees during the Hellenistic period, and later, in the 18th and 19th centuries, the use of the Hebrew word 'Yahadut' developed under the influence of German and the 'Wissenschaft des Judentums' movement.",
    "D": "The first use of the term 'Judaism' was by the rabbis in the sense of rejecting idolatry, and it retained a negative meaning until modern times.",
    "E": "Tertullian coined the term 'Judaism' in the 20th century during a Christian-Jewish polemic, and the word became a derogatory name for Jews only in that period."
  },
  "correct_answer": "C"
}
""",
        lang =  ARTICALES["Origin_of_the_name_Judaism"]["language"],
        glossary = ARTICALES["Origin_of_the_name_Judaism"]["glossary"]),
     "assistant": ONE_SHOT_MCQ_IMPROVE_PAIRS[0]["assistant"],
     "language": ARTICALES["Origin_of_the_name_Judaism"]["language"]},
    {"user": PromptBuilder().fix_language_prompt(
        article_content = ARTICALES["Supervised_learning"]["content"],
        question_text = """{
  "question": "איזו מהאפשרויות הבאות מתארת בצורה הטובה ביותר כיצד אלגוריתם למידה מונחית משתמש בנתוני אימון כדי לבצע תחזיות מדויקות עבור קלטים חדשים שלא נראו קודם?",
  "options": {
    "A": "הוא מקבץ קלטים באמצעות טכניקות אשכול ומשתמש בקבוצות אלו כדי לחזות תוצאות עבור נתונים חדשים.",
    "B": "הוא משתמש במשוב מתגמולים או עונשים חיצוניים כדי לבחור את התחזיות הטובות ביותר לאורך זמן.",
    "C": "הוא בונה מודל מתמטי באמצעות דוגמאות אימון — שכל אחת מהן מיוצגת כוקטור או מערך — המאורגנות במטריצה, ובאמצעות אופטימיזציה חוזרת של פונקציית מטרה, לומד פונקציה החוזה פלטים עבור קלטים חדשים.",
    "D": "הוא מוצא דפוסים בנתונים לא מתויגים באמצעות עץ החלטה ומיישם את הדפוסים האלה כדי לבצע תחזיות.",
    "E": "הוא שומר בזיכרון את זוגות הקלט-פלט שבנתוני האימון ובוחר את ההתאמה הקרובה ביותר כאשר מתקבל קלט חדש."
  },
  "correct_answer": "C"
}
""",
        lang =  ARTICALES["Supervised_learning"]["language"],
        glossary = ARTICALES["Supervised_learning"]["glossary"]),
     "assistant": ONE_SHOT_MCQ_IMPROVE_PAIRS[1]["assistant"],
     "language": ARTICALES["Supervised_learning"]["language"]},
    {"user": PromptBuilder().fix_language_prompt(
        article_content = ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["content"],
        question_text = """{
  "question": "Which of the following options most accurately and completely describes the sequence of events and the position of the Ottoman Empire just before it potentially entered World War I?",
  "options": {
    "A": "The Ottoman Empire bought ships from Britain, received them on time, and strengthened its ties with Britain, supported by the navy's position.",
    "B": "Germany started the war, and the Ottoman Empire immediately joined it, used the ships it got from Britain, and attacked Russia.",
    "C": "Britain took over the ships the Ottomans had bought, which caused public anger in Turkey and weakened resistance to an alliance with Germany. A secret agreement was signed with Germany, but the empire did not join the war right away, claiming the sultan had not officially approved the agreement.",
    "D": "The Ottoman Empire remained completely neutral, did not form ties with any side, and rejected all efforts to persuade it to join a military alliance.",
    "E": "Enver Pasha, who was the Minister of War, managed contacts with Germany on his own, received the ships from Britain, and signed an alliance that took effect immediately and did not require any further approval."
  },
  "correct_answer": "C"
}
""",
        lang =  ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["language"],
        glossary = ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["glossary"]),
     "assistant": ONE_SHOT_MCQ_IMPROVE_PAIRS[2]["assistant"],
     "language": ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["language"]},
    {"user": PromptBuilder().fix_language_prompt(
        article_content = ARTICALES["Macroeconomics_Outout_and_income"]["content"],
        question_text = """{
  "question": "איזו מהמשפטים מסבירה בצורה הטובה ביותר את הקשר בין תוצר מקומי גולמי (תמ\"ג), הכנסה לאומית גולמית (תל\"ג), והתפוקה הלאומית?",
  "options": {
    "A": "תמ\"ג מודד את סך הייצור בתוך המדינה, ותל\"ג מוסיף לכך גם הכנסות שהתקבלו מחו\"ל. התפוקה הלאומית מתייחסת בדרך כלל לתמ\"ג.",
    "B": "תל\"ג כולל רק כסף שנשלח על ידי אנשים החיים בחו\"ל, בעוד שתמ\"ג כולל רק סחורות מיובאות. התפוקה הלאומית היא סכום של שניהם.",
    "C": "תפוקה לאומית פירושה מה שאנשים מרוויחים במדינות אחרות. תמ\"ג ותל\"ג אינם חלק מהחישוב הזה.",
    "D": "תמ\"ג ותל\"ג תמיד מודדים את אותו הדבר כי אין הכנסות שנכנסות מחו\"ל או יוצאות החוצה.",
    "E": "תמ\"ג כולל גם הכנסות מקומיות וגם מחו\"ל, אך תל\"ג כולל רק הכנסות מתוך המדינה."
  },
  "correct_answer": "A"
}
""",
        lang =  ARTICALES["Macroeconomics_Outout_and_income"]["language"],
        glossary = ARTICALES["Macroeconomics_Outout_and_income"]["glossary"]),
     "assistant": ONE_SHOT_MCQ_IMPROVE_PAIRS[3]["assistant"],
     "language": ARTICALES["Macroeconomics_Outout_and_income"]["language"]}   
]

ONE_SHOT_EXTERNAL_DEPENDENCY_PAIRS = [
    {"user": PromptBuilder().external_info_dependency_prompt(
        article_content=ARTICALES["Origin_of_the_name_Judaism"]["content"],
        question_text=ONE_SHOT_MCQ_IMPROVE_PAIRS[0]["assistant"],
        glossary=ARTICALES["Origin_of_the_name_Judaism"]["glossary"]),
     "assistant": """No""",
     "language": ARTICALES["Origin_of_the_name_Judaism"]["language"]},
    {"user": PromptBuilder().external_info_dependency_prompt(
        article_content=ARTICALES["Supervised_learning"]["content"],
        question_text="""{
  "question": "What are some common supervised learning algorithms used in image recognition tasks?",
  "options": {
    "A": "Support Vector Machines and Convolutional Neural Networks",
    "B": "K-Means Clustering and Decision Trees",
    "C": "Q-Learning and Genetic Algorithms",
    "D": "Apriori Algorithm and PageRank",
    "E": "Autoencoders and Principal Component Analysis"
  },
  "correct_answer": "A"
}""",
        glossary=ARTICALES["Supervised_learning"]["glossary"]),
     "assistant": """Yes""",
     "language": ARTICALES["Supervised_learning"]["language"]},
    {"user": PromptBuilder().external_info_dependency_prompt(
        article_content=ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["content"],
        question_text="""{
  "question": "מה הייתה תגובתה של רוסיה להפקעת האוניות העות'מאניות על ידי בריטניה ערב מלחמת העולם הראשונה?",
  "options": {
    "A": "רוסיה גינתה את בריטניה והציעה לאימפריה העות'מאנית להצטרף אליה בברית.",
    "B": "רוסיה לא הגיבה רשמית אך הגבירה את נוכחותה הימית בים השחור.",
    "C": "רוסיה ניסתה לשכנע את האימפריה העות'מאנית להישאר נייטרלית.",
    "D": "רוסיה הודיעה שתתקוף את האימפריה העות'מאנית אם תתקרב לגרמניה.",
    "E": "אין מידע במאמר על תגובתה של רוסיה להפקעת האוניות."
  },
  "correct_answer": "E"
}""",
        glossary=ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["glossary"]),
     "assistant": """Yes""",
     "language": ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["language"]},
    {"user": PromptBuilder().external_info_dependency_prompt(
        article_content=ARTICALES["Macroeconomics_Outout_and_income"]["content"],
        question_text=ONE_SHOT_MCQ_IMPROVE_PAIRS[3]["assistant"],
        glossary=ARTICALES["Macroeconomics_Outout_and_income"]["glossary"]),
     "assistant": """No""",
     "language": ARTICALES["Macroeconomics_Outout_and_income"]["language"]}
]

ONE_SHOT_VALIDATE_FORMAT_PAIRS = [
    {"user": PromptBuilder().validate_question_format_prompt(
        question_text=ONE_SHOT_MCQ_CONVERSION_TO_JSON_PAIRS[0]["assistant"]
        ),
     "assistant": """Yes""",
     "language": ARTICALES["Origin_of_the_name_Judaism"]["language"]},
    {"user": PromptBuilder().validate_question_format_prompt(
        question_text=ONE_SHOT_MCQ_CONVERSION_TO_JSON_PAIRS[1]["assistant"]
        ),
    "assistant": """Yes""",
    "language": ARTICALES["Supervised_learning"]["language"]},
    {"user": PromptBuilder().validate_question_format_prompt(
        question_text="""{
"question": "מה מהבאים מתאר בצורה הנכונה והשלמה ביותר את השתלשלות האירועים והעמדות של האימפריה העות'מאנית ערב כניסתה האפשרית למלחמת העולם הראשונה?",
"options": [
"A": "האימפריה העות'מאנית תמכה באופן גורף בברית עם בריטניה, רכשה ממנה אוניות מלחמה, וקיבלה אותן בהצלחה למרות המצב הביטחוני המתוח.",
"B": "בעקבות הכרזת גרמניה מלחמה על רוסיה, האימפריה העות'מאנית הכריזה מיד על מלחמה גם היא, והפעילה את אוניות המלחמה שרכשה מבריטניה כנגד הצי הרוסי.",
"C": "הפקעת אוניות המלחמה שרכשה האימפריה העות'מאנית מבריטניה על ידי צ'רצ'יל גרמה לזעם רב בטורקיה, החלישה את ההתנגדות לברית עם גרמניה, אך למרות חתימת ברית סודית עם גרמניה, לא הצטרפה האימפריה מיד למלחמה בטענה שהחוזה לא אושר על ידי הסולטאן.",
"D": "האימפריה העות'מאנית הכריזה על נייטרליות מלאה ונמנעה מלבצע כל מגעים מדיניים עם גרמניה או בריטניה, למרות ניסיונות חוזרים לשכנעה להצטרף לברית צבאית.",       
"E": "אֶנווֶר פאשה, שר הימייה העות'מאני, ניהל לבדו את כל המגעים עם גרמניה, קיבל את האוניות מבריטניה, וחתם על חוזה ברית שהופעל מידית ללא צורך באישור נוסף."      
],
"correct_answer": "C"
}"""
        ),
     "assistant": """No""",
     "language": ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["language"]},
    {"user": PromptBuilder().validate_question_format_prompt(
        question_text="""{
"question": "Which of the following statements best describes the relationship between gross domestic product (GDP), gross national income (GNI), and national output?",
"options": {
"A": "GDP measures the total value of foreign investments held by a country, while GNI excludes any income from abroad.",
"B": "National output refers only to services produced within a country, and is not included in GDP or GNI.",
"C": "National output is the total production in a country, usually measured by GDP; GNI is calculated by adding net factor incomes from abroad to GDP, representing total income of all residents.",
"D": "GNI is always equal to GDP because foreign income has no impact on a country's total income.",
"E": "GDP includes both domestic and international production, while GNI measures only what is produced within national borders.",
"F": "National output is the value of all goods produced abroad by a country's companies, while GDP and GNI exclude any foreign contributions."
},
"correct_answer": "C"
}"""
        ),
     "assistant": """No""",
     "language": ARTICALES["Macroeconomics_Outout_and_income"]["language"]}
]

ONE_SHOT_VALIDATE_RELEVENCE_PAIRS = [
    {"user": PromptBuilder().validate_relevance_prompt(
        article_content=ARTICALES["Origin_of_the_name_Judaism"]["content"],
        question_text=ONE_SHOT_MCQ_CONVERSION_TO_JSON_PAIRS[2]["assistant"],
        glossary=ARTICALES["Origin_of_the_name_Judaism"]["glossary"]),
     "assistant": """3""",
     "language": ARTICALES["Origin_of_the_name_Judaism"]["language"]},
    {"user": PromptBuilder().validate_relevance_prompt(
        article_content=ARTICALES["Supervised_learning"]["content"],
        question_text="""{
  "question": "What term is used in the article to describe the individual data points within the training data?",
  "options": {
    "A": "Feature vector",
    "B": "Array",
    "C": "Training examples",
    "D": "Matrix",
    "E": "Predictions"
  },
  "correct_answer": "C"
}
""",
        glossary=ARTICALES["Supervised_learning"]["glossary"]),
        "assistant": """6""",
        "language": ARTICALES["Supervised_learning"]["language"]},
    {"user": PromptBuilder().validate_relevance_prompt(
        article_content=ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["content"],
        question_text=ONE_SHOT_MCQ_CONVERSION_TO_JSON_PAIRS[2]["assistant"],
        glossary=ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["glossary"]),
        "assistant": """10""",
        "language": ARTICALES["The_Ottoman_Empire_on_the_Eve_of_World_War_I"]["language"]},
    {"user": PromptBuilder().validate_relevance_prompt(
        article_content=ARTICALES["Macroeconomics_Outout_and_income"]["content"],
        question_text=ONE_SHOT_MCQ_CONVERSION_TO_JSON_PAIRS[3]["assistant"],
        glossary=ARTICALES["Macroeconomics_Outout_and_income"]["glossary"]),
        "assistant": """10""",
        "language": ARTICALES["Macroeconomics_Outout_and_income"]["language"]}
]

ONE_SHOT_CHECK_GRAMMER_PAIRS = [
    
]

ONE_SHOT_FIX_GRAMMER_PAIRS = [
    
]


class OneShotPairsProvider:
    """
    A class to provide one-shot pairs for various tasks.
    """
    def __init__(self, keys: List[str] = ["A", "B", "C", "D", "E"]):
        self.prompt_builder = PromptBuilder(keys)

    @staticmethod
    def get_random_mcq_creation_one_shot_pairs(n: int, lang: str = "auto") -> List[Tuple[str, str]]:
        """
        Return n random one-shot pairs for MCQ creation, filtered by language if specified.
        """
        pool = ONE_SHOT_MCQ_CREATION_PAIRS
        if lang != "auto":
            pool = [pair for pair in pool if pair.get("language") == lang]
        n = min(n, len(pool))
        
        # Strip 'language' before returning
        selected = random.sample(pool, n)
        stripped = [{"user": p["user"], "assistant": p["assistant"]} for p in selected]
        
        return stripped
    
    @staticmethod
    def get_random_mcq_conversion_one_shot_pairs(n: int, lang: str = "auto") -> List[Tuple[str, str]]:
        """
        Return n random one-shot pairs for MCQ conversion to JSON, filtered by language if specified.
        """
        pool = ONE_SHOT_MCQ_CONVERSION_TO_JSON_PAIRS
        if lang != "auto":
            pool = [pair for pair in pool if pair.get("language") == lang]
        n = min(n, len(pool))

        # Strip 'language' before returning
        selected = random.sample(pool, n)
        stripped = [{"user": p["user"], "assistant": p["assistant"]} for p in selected]

        return stripped
    
    @staticmethod
    def get_random_mcq_list_errors_one_shot_pairs(n: int, lang: str = "auto") -> List[Tuple[str, str]]:
        """
        Return n random one-shot pairs for MCQ list errors, filtered by language if specified.
        """
        pool = ONE_SHOT_MCQ_LIST_ERRORS_PAIRS
        if lang != "auto":
            pool = [pair for pair in pool if pair.get("language") == lang]
        n = min(n, len(pool))
        
        # Strip 'language' before returning
        selected = random.sample(pool, n)
        stripped = [{"user": p["user"], "assistant": p["assistant"]} for p in selected]
        
        return stripped
    
    @staticmethod
    def get_random_mcq_improve_one_shot_pairs(n: int, lang: str = "auto") -> List[Tuple[str, str]]:
        """
        Return n random one-shot pairs for MCQ improvement, filtered by language if specified.
        """
        pool = ONE_SHOT_MCQ_IMPROVE_PAIRS
        if lang != "auto":
            pool = [pair for pair in pool if pair.get("language") == lang]
        n = min(n, len(pool))
        
        # Strip 'language' before returning
        selected = random.sample(pool, n)
        stripped = [{"user": p["user"], "assistant": p["assistant"]} for p in selected]
        
        return stripped
    
    @staticmethod
    def get_random_answer_mcq_one_shot_pairs(n: int, lang: str = "auto") -> List[Tuple[str, str]]:
        """
        Return n random one-shot pairs for MCQ answer, filtered by language if specified.
        """
        pool = ONE_SHOT_ANSWER_MCQ_PAIRS
        if lang != "auto":
            pool = [pair for pair in pool if pair.get("language") == lang]
        n = min(n, len(pool))
        
        # Strip 'language' before returning
        selected = random.sample(pool, n)
        stripped = [{"user": p["user"], "assistant": p["assistant"]} for p in selected]
        
        return stripped
    
    @staticmethod
    def get_random_validate_format_one_shot_pairs(n: int, lang: str = "auto") -> List[Tuple[str, str]]:
        """
        Return n random one-shot pairs for validating question format, filtered by language if specified.
        """
        pool = ONE_SHOT_VALIDATE_FORMAT_PAIRS
        if lang != "auto":
            pool = [pair for pair in pool if pair.get("language") == lang]
        n = min(n, len(pool))

        # Strip 'language' before returning
        selected = random.sample(pool, n)
        stripped = [{"user": p["user"], "assistant": p["assistant"]} for p in selected]

        return stripped
    
    @staticmethod
    def get_random_external_dependency_one_shot_pairs(n: int, lang: str = "auto") -> List[Tuple[str, str]]:
        """
        Return n random one-shot pairs for external dependency checks, filtered by language if specified.
        """
        pool = ONE_SHOT_EXTERNAL_DEPENDENCY_PAIRS
        if lang != "auto":
            pool = [pair for pair in pool if pair.get("language") == lang]
        n = min(n, len(pool))

        # Strip 'language' before returning
        selected = random.sample(pool, n)
        stripped = [{"user": p["user"], "assistant": p["assistant"]} for p in selected]

        return stripped
    
    @staticmethod
    def get_random_validate_relevance_one_shot_pairs(n: int, lang: str = "auto") -> List[Tuple[str, str]]:
        """
        Return n random one-shot pairs for validating relevance, filtered by language if specified.
        """
        pool = ONE_SHOT_VALIDATE_RELEVENCE_PAIRS
        if lang != "auto":
            pool = [pair for pair in pool if pair.get("language") == lang]
        n = min(n, len(pool))

        # Strip 'language' before returning
        selected = random.sample(pool, n)
        stripped = [{"user": p["user"], "assistant": p["assistant"]} for p in selected]

        return stripped
    
    @staticmethod
    def get_random_validate_language_one_shot_pairs(n: int, lang: str = "auto") -> List[Tuple[str, str]]:
        """
        Return n random one-shot pairs for validating language, filtered by language if specified.
        """
        pool = ONE_SHOT_VALIDATE_LANGUAGE_PAIRS
        if lang != "auto":
            pool = [pair for pair in pool if pair.get("language") == lang]
        n = min(n, len(pool))

        # Strip 'language' before returning
        selected = random.sample(pool, n)
        stripped = [{"user": p["user"], "assistant": p["assistant"]} for p in selected]

        return stripped
    
    @staticmethod
    def get_random_fix_language_one_shot_pairs(n: int, lang: str = "auto") -> List[Tuple[str, str]]:
        """
        Return n random one-shot pairs for fixing language, filtered by language if specified.
        """
        pool = ONE_SHOT_FIX_LANGUAGE_PAIRS
        if lang != "auto":
            pool = [pair for pair in pool if pair.get("language") == lang]
        n = min(n, len(pool))

        # Strip 'language' before returning
        selected = random.sample(pool, n)
        stripped = [{"user": p["user"], "assistant": p["assistant"]} for p in selected]

        return stripped