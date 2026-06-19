import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from core.models import SeaArea, Farmer, Cage, CageFarmer
from inspection.models import InspectionRoute, InspectionRecord, InspectionPoint
from disease.models import DiseaseReport, MortalityReport


class Command(BaseCommand):
    help = '创建初始测试数据'

    def handle(self, *args, **options):
        self.stdout.write('开始创建初始数据...')

        self.create_superuser()
        self.create_sea_areas()
        self.create_farmers()
        self.create_cages()
        self.create_cage_farmer_relations()
        self.create_inspection_routes()
        self.create_inspection_records()
        self.create_disease_reports()
        self.create_mortality_reports()

        self.stdout.write(self.style.SUCCESS('初始数据创建完成！'))

    def create_superuser(self):
        self.stdout.write('创建超级用户...')
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123456'
            )
            self.stdout.write(self.style.SUCCESS('  超级用户创建成功: admin / admin123456'))
        else:
            self.stdout.write('  超级用户已存在')

    def create_sea_areas(self):
        self.stdout.write('创建海区数据...')
        sea_areas_data = [
            {
                'name': '东海区A区',
                'location': '浙江省舟山市普陀区',
                'area': 500.50,
                'depth': 25.5,
                'lat_min': 29.5,
                'lat_max': 30.2,
                'lng_min': 121.8,
                'lng_max': 122.5,
                'description': '主要养殖大黄鱼、石斑鱼等优质海水鱼'
            },
            {
                'name': '东海区B区',
                'location': '浙江省宁波市象山县',
                'area': 380.25,
                'depth': 18.0,
                'lat_min': 29.0,
                'lat_max': 29.6,
                'lng_min': 121.5,
                'lng_max': 122.0,
                'description': '主要养殖鲈鱼、黑鲷等'
            },
            {
                'name': '南海区A区',
                'location': '广东省深圳市大鹏新区',
                'area': 620.00,
                'depth': 30.0,
                'lat_min': 22.3,
                'lat_max': 22.8,
                'lng_min': 114.3,
                'lng_max': 114.9,
                'description': '主要养殖石斑鱼、金枪鱼等热带鱼类'
            },
            {
                'name': '黄渤海区A区',
                'location': '山东省烟台市蓬莱区',
                'area': 450.75,
                'depth': 20.0,
                'lat_min': 37.5,
                'lat_max': 38.0,
                'lng_min': 120.5,
                'lng_max': 121.0,
                'description': '主要养殖海参、鲍鱼、扇贝等海珍品'
            },
            {
                'name': '福建省三都澳海区',
                'location': '福建省宁德市蕉城区',
                'area': 720.00,
                'depth': 15.0,
                'lat_min': 26.4,
                'lat_max': 26.8,
                'lng_min': 119.4,
                'lng_max': 119.9,
                'description': '中国最大的大黄鱼养殖基地'
            }
        ]

        for data in sea_areas_data:
            SeaArea.objects.get_or_create(name=data['name'], defaults=data)
        self.stdout.write(f'  海区数据创建完成，共 {SeaArea.objects.count()} 条')

    def create_farmers(self):
        self.stdout.write('创建养殖户数据...')
        sea_areas = list(SeaArea.objects.all())
        farmers_data = [
            {'name': '张三', 'phone': '13800138001', 'id_card': '330901198001010001', 'scale': '大型', 'registration_date': '2020-01-15'},
            {'name': '李四', 'phone': '13800138002', 'id_card': '330901198502020002', 'scale': '中型', 'registration_date': '2020-03-20'},
            {'name': '王五', 'phone': '13800138003', 'id_card': '330901199003030003', 'scale': '小型', 'registration_date': '2020-05-10'},
            {'name': '赵六', 'phone': '13800138004', 'id_card': '440301198204040004', 'scale': '大型', 'registration_date': '2019-08-15'},
            {'name': '钱七', 'phone': '13800138005', 'id_card': '440301198705050005', 'scale': '中型', 'registration_date': '2020-02-28'},
            {'name': '孙八', 'phone': '13800138006', 'id_card': '370601198306060006', 'scale': '中型', 'registration_date': '2019-11-20'},
            {'name': '周九', 'phone': '13800138007', 'id_card': '352201198607070007', 'scale': '大型', 'registration_date': '2018-06-15'},
            {'name': '吴十', 'phone': '13800138008', 'id_card': '330201199208080008', 'scale': '小型', 'registration_date': '2021-01-10'},
            {'name': '郑十一', 'phone': '13800138009', 'id_card': '330901198809090009', 'scale': '中型', 'registration_date': '2020-09-05'},
            {'name': '王十二', 'phone': '13800138010', 'id_card': '352201199110100010', 'scale': '大型', 'registration_date': '2019-04-18'},
        ]

        for i, data in enumerate(farmers_data):
            data['sea_area'] = sea_areas[i % len(sea_areas)]
            data['contact_info'] = f'联系人：{data["name"]}，备用电话：{data["phone"]}'
            Farmer.objects.get_or_create(id_card=data['id_card'], defaults=data)
        self.stdout.write(f'  养殖户数据创建完成，共 {Farmer.objects.count()} 条')

    def create_cages(self):
        self.stdout.write('创建网箱数据...')
        sea_areas = list(SeaArea.objects.all())
        species_list = ['大黄鱼', '石斑鱼', '鲈鱼', '黑鲷', '真鲷', '军曹鱼', '卵形鲳鲹', '红甘鱼']
        status_list = ['normal', 'normal', 'normal', 'normal', 'maintenance', 'empty', 'abnormal']

        cage_count = 0
        for sea_area in sea_areas:
            for i in range(1, 9):
                code = f'{sea_area.name[:2]}-{i:03d}'
                cage_data = {
                    'code': code,
                    'sea_area': sea_area,
                    'location': f'{sea_area.location} {i}号网箱',
                    'capacity': random.randint(1000, 10000),
                    'species': random.choice(species_list),
                    'stocking_date': timezone.now().date() - timedelta(days=random.randint(30, 365)),
                    'status': random.choice(status_list),
                    'area': round(random.uniform(100, 500), 2)
                }
                Cage.objects.get_or_create(code=code, defaults=cage_data)
                cage_count += 1
        self.stdout.write(f'  网箱数据创建完成，共 {cage_count} 条')

    def create_cage_farmer_relations(self):
        self.stdout.write('创建网箱-养殖户关联数据...')
        cages = list(Cage.objects.all())
        farmers = list(Farmer.objects.all())

        for cage in cages:
            assigned_farmers = random.sample(farmers, random.randint(1, 3))
            for farmer in assigned_farmers:
                CageFarmer.objects.get_or_create(
                    cage=cage,
                    farmer=farmer,
                    defaults={
                        'start_date': timezone.now().date() - timedelta(days=random.randint(30, 365)),
                    }
                )
        self.stdout.write(f'  网箱-养殖户关联数据创建完成，共 {CageFarmer.objects.count()} 条')

    def create_inspection_routes(self):
        self.stdout.write('创建巡检路线数据...')
        sea_areas = list(SeaArea.objects.all())
        routes_data = [
            {'name': '日常巡检路线A', 'description': '覆盖东区主要养殖区', 'creator': '系统管理员'},
            {'name': '重点监控路线B', 'description': '针对高风险区域的巡检', 'creator': '系统管理员'},
            {'name': '水质监测路线C', 'description': '定期水质检测路线', 'creator': '技术人员'},
            {'name': '病害排查路线D', 'description': '病害发生时的紧急排查', 'creator': '技术人员'},
        ]

        for data in routes_data:
            route, created = InspectionRoute.objects.get_or_create(name=data['name'], defaults=data)
            if created:
                area = random.choice(sea_areas)
                cages = list(area.cages.all())
                if cages:
                    selected_cages = random.sample(cages, min(5, len(cages)))
                    for idx, cage in enumerate(selected_cages):
                        from inspection.models import InspectionRouteCage
                        InspectionRouteCage.objects.get_or_create(
                            route=route,
                            cage=cage,
                            defaults={'order': idx}
                        )
        self.stdout.write(f'  巡检路线数据创建完成，共 {InspectionRoute.objects.count()} 条')

    def create_inspection_records(self):
        self.stdout.write('创建巡检记录数据...')
        routes = list(InspectionRoute.objects.all())
        inspectors = ['巡检员小王', '巡检员小李', '巡检员小张', '技术人员小陈']
        status_list = ['pending', 'in_progress', 'completed', 'completed', 'completed', 'cancelled']

        for i in range(20):
            route = random.choice(routes)
            status = random.choice(status_list)
            start_time = timezone.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
            end_time = start_time + timedelta(hours=random.randint(1, 6)) if status in ['completed', 'cancelled'] else None

            record_data = {
                'route': route,
                'inspector': random.choice(inspectors),
                'start_time': start_time,
                'end_time': end_time,
                'status': status,
                'remarks': f'第{i+1}次巡检记录' if random.random() > 0.3 else ''
            }
            record = InspectionRecord.objects.create(**record_data)

            if status == 'completed':
                route_cages = list(route.cages.all())
                for cage in route_cages:
                    has_abnormality = random.random() < 0.15
                    point_data = {
                        'record': record,
                        'cage': cage,
                        'check_time': start_time + timedelta(minutes=random.randint(10, 60)),
                        'water_temperature': round(random.uniform(18, 30), 2),
                        'salinity': round(random.uniform(25, 35), 2),
                        'ph_value': round(random.uniform(7.5, 8.5), 2),
                        'water_quality': random.choice(['excellent', 'good', 'good', 'fair']),
                        'abnormal_condition': '发现少量鱼体表面有损伤，需要进一步观察' if has_abnormality else '',
                    }
                    InspectionPoint.objects.create(**point_data)
        self.stdout.write(f'  巡检记录数据创建完成，共 {InspectionRecord.objects.count()} 条')
        self.stdout.write(f'  巡检点数据创建完成，共 {InspectionPoint.objects.count()} 条')

    def create_disease_reports(self):
        self.stdout.write('创建病害上报数据...')
        cages = list(Cage.objects.all())
        reporters = ['养殖户张三', '养殖户李四', '巡检员小王', '技术人员小陈']
        disease_types = ['bacterial', 'viral', 'parasitic', 'fungal', 'nutritional', 'environmental', 'other']
        severities = ['mild', 'moderate', 'severe', 'critical']
        statuses = ['pending', 'processing', 'resolved', 'closed']
        disease_descriptions = {
            'bacterial': '发现鱼体表面有出血点，肛门红肿，疑似细菌性感染',
            'viral': '鱼群出现异常死亡，鱼体发黑，游动缓慢，疑似病毒性疾病',
            'parasitic': '鱼体表面有白点，鳃部粘液增多，疑似寄生虫感染',
            'fungal': '鱼体表面有棉絮状附着物，疑似真菌感染',
            'nutritional': '鱼群生长缓慢，体型消瘦，疑似营养问题',
            'environmental': '水质突变，鱼群出现应激反应',
            'other': '发现异常情况，原因待查'
        }

        for i in range(15):
            cage = random.choice(cages)
            disease_type = random.choice(disease_types)
            status = random.choice(statuses)
            report_data = {
                'cage': cage,
                'reporter': random.choice(reporters),
                'disease_type': disease_type,
                'severity': random.choice(severities),
                'description': disease_descriptions[disease_type],
                'status': status,
                'treated_by': '兽医王医生' if status in ['processing', 'resolved', 'closed'] else None,
                'treatment_method': '使用抗生素治疗，改善水质环境' if status in ['processing', 'resolved', 'closed'] else None,
                'treatment_time': timezone.now() if status in ['processing', 'resolved', 'closed'] else None,
            }
            report = DiseaseReport.objects.create(**report_data)
            report.report_time = timezone.now() - timedelta(days=random.randint(0, 30))
            report.save()
        self.stdout.write(f'  病害上报数据创建完成，共 {DiseaseReport.objects.count()} 条')

    def create_mortality_reports(self):
        self.stdout.write('创建死亡上报数据...')
        cages = list(Cage.objects.all())
        reporters = ['养殖户张三', '养殖户李四', '巡检员小王', '技术人员小陈']
        causes = ['disease', 'predation', 'environment', 'feeding', 'operation', 'unknown', 'other']
        statuses = ['pending', 'processing', 'resolved', 'closed']
        descriptions = {
            'disease': '因疾病导致死亡，已采取治疗措施',
            'predation': '发现敌害生物入侵，造成部分鱼类死亡',
            'environment': '水质突变导致鱼类应激死亡',
            'feeding': '投喂不当导致消化不良死亡',
            'operation': '操作不当造成机械损伤死亡',
            'unknown': '死亡原因不明，正在调查中',
            'other': '其他原因导致死亡'
        }

        for i in range(12):
            cage = random.choice(cages)
            cause = random.choice(causes)
            status = random.choice(statuses)
            report_data = {
                'cage': cage,
                'reporter': random.choice(reporters),
                'mortality_count': random.randint(10, 500),
                'cause': cause,
                'description': descriptions[cause],
                'status': status,
                'treated_by': '技术员小李' if status in ['processing', 'resolved', 'closed'] else None,
                'treatment_method': '清理死鱼，消毒网箱，调整投喂方案' if status in ['processing', 'resolved', 'closed'] else None,
                'treatment_time': timezone.now() if status in ['processing', 'resolved', 'closed'] else None,
            }
            report = MortalityReport.objects.create(**report_data)
            report.report_time = timezone.now() - timedelta(days=random.randint(0, 30))
            report.save()
        self.stdout.write(f'  死亡上报数据创建完成，共 {MortalityReport.objects.count()} 条')
