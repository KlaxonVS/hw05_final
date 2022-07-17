from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    template_name = 'about/basic_about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Об авторе проекта'
        context['text'] = ('Тут я размещу информацию о себе, '
                           'используя свои умения верстать. '
                           'Картинки, блоки, элементы бустрап. '
                           'А может быть, просто напишу несколько абзацев '
                           'текста, правда.'
                           )
        return context


class AboutTechView(TemplateView):
    template_name = 'about/basic_about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Технологии'
        context['text'] = ('Для создания этого сайта использовались:')
        context['list'] = (['Python', 'Django'])
        return context
