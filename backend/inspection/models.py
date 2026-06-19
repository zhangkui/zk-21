from django.db import models
from core.models import Cage


class InspectionRoute(models.Model):
    name = models.CharField(max_length=200, verbose_name='路线名称')
    description = models.TextField(null=True, blank=True, verbose_name='描述')
    cages = models.ManyToManyField(Cage, through='InspectionRouteCage', related_name='routes', verbose_name='包含的网箱')
    creator = models.CharField(max_length=100, null=True, blank=True, verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'inspection_route'
        verbose_name = '巡检路线'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class InspectionRouteCage(models.Model):
    route = models.ForeignKey(InspectionRoute, on_delete=models.CASCADE, verbose_name='巡检路线')
    cage = models.ForeignKey(Cage, on_delete=models.CASCADE, verbose_name='网箱')
    order = models.IntegerField(default=0, verbose_name='顺序')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'inspection_route_cage'
        verbose_name = '巡检路线-网箱关联'
        verbose_name_plural = verbose_name
        ordering = ['order']
        unique_together = ('route', 'cage')


class InspectionRecord(models.Model):
    STATUS_CHOICES = [
        ('pending', '待开始'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]

    route = models.ForeignKey(InspectionRoute, on_delete=models.PROTECT, related_name='records', verbose_name='巡检路线')
    inspector = models.CharField(max_length=100, verbose_name='巡检人')
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    remarks = models.TextField(null=True, blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'inspection_record'
        verbose_name = '巡检记录'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.route.name} - {self.inspector} - {self.created_at.strftime("%Y-%m-%d")}'


class InspectionPoint(models.Model):
    WATER_QUALITY_CHOICES = [
        ('excellent', '优秀'),
        ('good', '良好'),
        ('fair', '一般'),
        ('poor', '较差'),
        ('very_poor', '很差'),
    ]

    record = models.ForeignKey(InspectionRecord, on_delete=models.CASCADE, related_name='points', verbose_name='巡检记录')
    cage = models.ForeignKey(Cage, on_delete=models.PROTECT, related_name='inspection_points', verbose_name='网箱')
    check_time = models.DateTimeField(verbose_name='检查时间')
    water_temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='水温(°C)')
    salinity = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='盐度(‰)')
    ph_value = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, verbose_name='pH值')
    water_quality = models.CharField(max_length=50, choices=WATER_QUALITY_CHOICES, null=True, blank=True, verbose_name='水质情况')
    abnormal_condition = models.TextField(null=True, blank=True, verbose_name='异常情况')
    has_abnormality = models.BooleanField(default=False, verbose_name='是否有异常')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'inspection_point'
        verbose_name = '巡检点'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.record.id} - {self.cage.code} - {self.check_time}'

    def save(self, *args, **kwargs):
        if self.abnormal_condition and len(self.abnormal_condition.strip()) > 0:
            self.has_abnormality = True
        super().save(*args, **kwargs)
