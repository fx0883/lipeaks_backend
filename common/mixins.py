"""
通用Mixin类
"""
from common.utils.image_url import normalize_image_path


class ImageFieldNormalizerMixin:
    """
    自动标准化图片字段的Mixin
    
    使用方法：
    1. 继承此Mixin（放在第一个位置）
    2. 定义 image_fields = ['cover_image', 'avatar'] 等
    3. validate方法会自动处理这些字段，将URL标准化为相对路径
    
    示例：
        class ArticleSerializer(ImageFieldNormalizerMixin, serializers.ModelSerializer):
            image_fields = ['cover_image', 'cover_image_small']
    """
    image_fields = []
    
    def validate(self, data):
        """验证并标准化图片字段"""
        # 调用父类的validate方法
        data = super().validate(data)
        
        # 获取请求对象
        request = self.context.get('request')
        
        # 如果有请求对象，处理所有定义的图片字段
        if request:
            for field_name in self.image_fields:
                if field_name in data and data[field_name]:
                    data[field_name] = normalize_image_path(
                        data[field_name], 
                        request
                    )
        
        return data
