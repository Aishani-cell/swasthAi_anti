import os, shutil

os.makedirs('frontend/legacy_pages', exist_ok=True)
keep = {'01_Login.py', '03_Register_Patient.py', '04_Search_Patients.py', '05_Encounter_Form.py', '__init__.py'}
for f in os.listdir('frontend/pages'):
    if f not in keep and f != '__pycache__':
        src = os.path.join('frontend/pages', f)
        dst = os.path.join('frontend/legacy_pages', f)
        print('Archiving:', f)
        if os.path.exists(dst):
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            else:
                os.remove(dst)
        shutil.move(src, dst)
print('Legacy pages safely archived in frontend/legacy_pages.')
