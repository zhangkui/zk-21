from django.db import models


class SeaArea(models.Model):
    name = models.CharField(max_length=200, verbose_name='海区名称')
    location = models.CharField(max_length=500, verbose_name='位置')
    area = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='面积(公顷)')
    depth = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='平均水深(米)')
    lat_min = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, verbose_name='纬度最小值')
    lat_max = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, verbose_name='纬度最大值')
    lng_min = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, verbose_name='经度最小值')
    lng_max = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, verbose_name='经度最大值')
    boundary = models.JSONField(null=True, blank=True, verbose_name='边界坐标(多边形点集合)')
    description = models.TextField(null=True, blank=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'core_seaarea'
        verbose_name = '海区'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Farmer(models.Model):
    name = models.CharField(max_length=100, verbose_name='姓名')
    phone = models.CharField(max_length=20, verbose_name='联系电话')
    id_card = models.CharField(max_length=18, unique=True, verbose_name='身份证号')
    sea_area = models.ForeignKey(SeaArea, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='所属海区', related_name='farmers')
    scale = models.CharField(max_length=100, null=True, blank=True, verbose_name='养殖规模')
    registration_date = models.DateField(null=True, blank=True, verbose_name='注册日期')
    contact_info = models.TextField(null=True, blank=True, verbose_name='其他联系方式')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'core_farmer'
        verbose_name = '养殖户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Cage(models.Model):
    STATUS_CHOICES = [
        ('normal', '正常'),
        ('maintenance', '维护中'),
        ('empty', '空置'),
        ('abnormal', '异常'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name='网箱编号')
    sea_area = models.ForeignKey(SeaArea, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='所属海区', related_name='cages')
    location = models.CharField(max_length=500, verbose_name='位置')
    capacity = models.IntegerField(default=0, verbose_name='容量(尾)')
    species = models.CharField(max_length=200, null=True, blank=True, verbose_name='养殖品种')
    stocking_date = models.DateField(null=True, blank=True, verbose_name='投放日期')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='normal', verbose_name='状态')
    area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='面积(平方米)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'core_cage'
        verbose_name = '网箱'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.code


class CageFarmer(models.Model):
    cage = models.ForeignKey(Cage, on_delete=models.CASCADE, verbose_name='网箱', related_name='cage_farmers')
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, verbose_name='养殖户', related_name='cage_farmers')
    start_date = models.DateField(null=True, blank=True, verbose_name='开始日期')
    end_date = models.DateField(null=True, blank=True, verbose_name='结束日期')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'core_cagefarmer'
        verbose_name = '网箱-养殖户关联'
        verbose_name_plural = verbose_name
        unique_together = ('cage', 'farmer')

    def __str__(self):
        return f'{self.cage.code} - {self.farmer.name}'
