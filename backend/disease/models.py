from django.db import models
from django.conf import settings
from core.models import Cage


def disease_image_upload_path(instance, filename):
    return f'disease/{instance.cage.id}/{filename}'


def mortality_image_upload_path(instance, filename):
    return f'mortality/{instance.cage.id}/{filename}'


class DiseaseReport(models.Model):
    SEVERITY_CHOICES = [
        ('mild', '轻微'),
        ('moderate', '中等'),
        ('severe', '严重'),
        ('critical', '危急'),
    ]

    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('resolved', '已解决'),
        ('closed', '已关闭'),
    ]

    DISEASE_TYPES = [
        ('bacterial', '细菌性疾病'),
        ('viral', '病毒性疾病'),
        ('parasitic', '寄生虫病'),
        ('fungal', '真菌性疾病'),
        ('nutritional', '营养性疾病'),
        ('environmental', '环境性疾病'),
        ('other', '其他'),
    ]

    cage = models.ForeignKey(Cage, on_delete=models.CASCADE, related_name='disease_reports', verbose_name='网箱')
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='disease_reports',
        verbose_name='上报人'
    )
    report_time = models.DateTimeField(auto_now_add=True, verbose_name='上报时间')
    disease_type = models.CharField(max_length=50, choices=DISEASE_TYPES, verbose_name='病害类型')
    severity = models.CharField(max_length=50, choices=SEVERITY_CHOICES, verbose_name='严重程度')
    image = models.ImageField(upload_to=disease_image_upload_path, null=True, blank=True, verbose_name='图片')
    description = models.TextField(verbose_name='病害描述')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    treated_by = models.CharField(max_length=100, null=True, blank=True, verbose_name='处理人')
    treatment_method = models.TextField(null=True, blank=True, verbose_name='处理方案')
    treatment_time = models.DateTimeField(null=True, blank=True, verbose_name='处理时间')
    is_anomaly = models.BooleanField(default=False, verbose_name='是否异常')
    anomaly_score = models.FloatField(default=0.0, verbose_name='异常分数')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'disease_report'
        verbose_name = '病害上报'
        verbose_name_plural = verbose_name
        ordering = ['-report_time']

    def __str__(self):
        return f'{self.cage.code} - {self.get_disease_type_display()} - {self.report_time.strftime("%Y-%m-%d")}'


class MortalityReport(models.Model):
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('resolved', '已解决'),
        ('closed', '已关闭'),
    ]

    CAUSE_CHOICES = [
        ('disease', '疾病'),
        ('predation', '敌害'),
        ('environment', '环境因素'),
        ('feeding', '投喂问题'),
        ('operation', '操作失误'),
        ('unknown', '原因不明'),
        ('other', '其他'),
    ]

    cage = models.ForeignKey(Cage, on_delete=models.CASCADE, related_name='mortality_reports', verbose_name='网箱')
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='mortality_reports',
        verbose_name='上报人'
    )
    report_time = models.DateTimeField(auto_now_add=True, verbose_name='上报时间')
    mortality_count = models.IntegerField(verbose_name='死亡数量(尾)')
    cause = models.CharField(max_length=50, choices=CAUSE_CHOICES, verbose_name='死亡原因')
    image = models.ImageField(upload_to=mortality_image_upload_path, null=True, blank=True, verbose_name='图片')
    description = models.TextField(verbose_name='情况描述')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    treated_by = models.CharField(max_length=100, null=True, blank=True, verbose_name='处理人')
    treatment_method = models.TextField(null=True, blank=True, verbose_name='处理方案')
    treatment_time = models.DateTimeField(null=True, blank=True, verbose_name='处理时间')
    is_anomaly = models.BooleanField(default=False, verbose_name='是否异常')
    anomaly_score = models.FloatField(default=0.0, verbose_name='异常分数')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'mortality_report'
        verbose_name = '死亡上报'
        verbose_name_plural = verbose_name
        ordering = ['-report_time']

    def __str__(self):
        return f'{self.cage.code} - 死亡{self.mortality_count}尾 - {self.report_time.strftime("%Y-%m-%d")}'
