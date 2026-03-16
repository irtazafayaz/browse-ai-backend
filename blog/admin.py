from django import forms
from django.contrib import admin
from .models import BlogPost


class BlogPostAdminForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 35, 'style': 'font-family: monospace; font-size: 13px;'}),
        help_text='Write content as HTML. Use &lt;h2&gt;, &lt;h3&gt;, &lt;p&gt;, &lt;ul&gt;, &lt;li&gt;, &lt;strong&gt; tags.',
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text='One or two sentences shown on the blog index card and in search engine results.',
    )

    class Meta:
        model = BlogPost
        fields = '__all__'


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    form = BlogPostAdminForm

    list_display = ['title', 'category', 'published', 'published_at', 'read_time']
    list_filter = ['published', 'category']
    list_editable = ['published']
    search_fields = ['title', 'description', 'content']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['updated_at']

    fieldsets = (
        ('Post Details', {
            'fields': ('title', 'slug', 'description', 'category', 'read_time', 'cover_image'),
        }),
        ('Content', {
            'fields': ('content',),
        }),
        ('Publishing', {
            'fields': ('published', 'published_at', 'updated_at'),
        }),
    )
