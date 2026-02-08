from django.contrib import admin

from .models import (
    Catagory, Blog, Tag, EmailSignUp, Contact, Comment, Reply, Like,
)


class CatAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


admin.site.register(Catagory, CatAdmin)
admin.site.register(Blog)
admin.site.register(Comment)
admin.site.register(Reply)
admin.site.register(Tag)
admin.site.register(EmailSignUp)
admin.site.register(Contact)
admin.site.register(Like)


# made by Nazrul Islam Yeasin 
# Facebook : https://facebook.com/yeazin.io
# Twitter : https://twitter.com/_yeazin
# Github : https://github.com/yeazin
# linked In : https://www.linkedin.com/in/yeazin/
# website : yeazin.github.io
