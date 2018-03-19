from .markdown import markdown
from .renderers import Mkd_html

def md2html(source):
	return markdown(source, Mkd_html())