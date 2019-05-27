import django_tables2 as tables


class PolicyTable(tables.Table):
    group = tables.Column('Policy', accessor='policy.group.description')
    policy = tables.Column('Description', accessor='policy.description')

    class Meta:
        attrs = {'class': 'table'}
        orderable = False
