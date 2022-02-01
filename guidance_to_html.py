import markdown
import yaml

with open('data_classification_questions.yml') as f:
    questions = yaml.load(f, Loader=yaml.FullLoader)

with open('questions.html',"w") as f:
    for q in questions:
        f.write(f"<h3 id='{q['name']}'>{q['name']}</h3>")
        if q.get('text'):
            f.write(markdown.markdown(q['text']).replace("\n",""))
            if q.get(True):
                f.write(f"<a href='#{q[True]}'>Yes</a>")
            if q.get(False):
                f.write(f"<a href='#{q[False]}'>No</a>")
        if q.get('guidance'):
            f.write("<h5>Guidance</h5>")
            f.write(markdown.markdown(q['guidance']).replace("\n",""))