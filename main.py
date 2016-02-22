import os
import webapp2
import jinja2
from google.appengine.ext import ndb
from google.appengine.api import taskqueue

# Initial jinja/templating set-up

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class MainHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        # params['user'] = self.user
        return render_str(template, **params)
        
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class BlogPost(ndb.Model):
  title = ndb.StringProperty()
  subject = ndb.TextProperty()
  created = ndb.DateTimeProperty(auto_now_add=True)
  views = ndb.IntegerProperty()

class FrontPage(MainHandler):
  def get(self):
    blog_posts = BlogPost.query().order(-BlogPost.created).fetch(10)
    self.render("front.html", blog_posts = blog_posts)

  def post(self):
    title = self.request.get('title')
    subject = self.request.get('subject')
    blog = BlogPost(title=title, subject=subject, views=1)
    blog.put()
    self.redirect('/')

class PostPage(MainHandler):
  def get(self, post_id):
    key = ndb.Key('BlogPost', int(post_id))
    post = key.get()
    postdict = post.to_dict()
    q = taskqueue.Queue('views')
    q.add(taskqueue.Task(payload=post_id, method='PULL'))
    self.render("permalink.html", postdict=postdict)

class ViewCount(webapp2.RequestHandler):
  def get(self):
    q = taskqueue.Queue('views')
    while True:
      tasks = q.lease_tasks(60, 1000)
      if not tasks:
        return
      tallies = {}
      for t in tasks:
        tallies[t.payload] = tallies.get(t.payload, 0) + 1
      objects = ndb.get_multi([ndb.Key(BlogPost, int(k)) for k in tallies])
      for object in objects:
        object.views += tallies[str(object.key.id())]
      ndb.put_multi(objects)
      q.delete_tasks(tasks)


app = webapp2.WSGIApplication([('/', FrontPage),
                               ('/([0-9]+)', PostPage),
                               ('/viewcount', ViewCount)
                               ],
                              debug=True)
