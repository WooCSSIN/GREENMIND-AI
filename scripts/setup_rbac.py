import sys
# Thêm thư mục gốc vào path để nhận diện 'core' và 'apps'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User, Group

def setup_rbac():
    # 1. Create Groups
    tech_group, _ = Group.objects.get_or_create(name='Technical')
    biz_group, _ = Group.objects.get_or_create(name='Business')
    admin_group, _ = Group.objects.get_or_create(name='Admin')
    
    print(f"Groups checked: {Group.objects.all()}")
    
    # 2. Create or Update TechAdmin
    u_tech, created = User.objects.get_or_create(username='tech_admin')
    if created:
        u_tech.set_password('GreenMind@2025')
        u_tech.save()
        print("Created User: tech_admin / GreenMind@2025")
    
    u_tech.groups.add(tech_group)
    print(f"Assigned 'Technical' group to '{u_tech.username}'")

    # 3. Create a Business User for testing
    u_biz, created = User.objects.get_or_create(username='biz_user')
    if created:
        u_biz.set_password('GreenMind@2025')
        u_biz.save()
        print("Created User: biz_user / GreenMind@2025")
    
    u_biz.groups.add(biz_group)
    print(f"Assigned 'Business' group to '{u_biz.username}'")

if __name__ == "__main__":
    setup_rbac()
