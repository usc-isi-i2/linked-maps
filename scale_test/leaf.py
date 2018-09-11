c = open('contain.csv')
f = open('a.csv')
l = open('leaf.csv','w')

next(c)
next(f)
l.write('uri,map\n')

ids = []
for i in f:
    tmp = i.strip().split(',')
    ids.append((tmp[3],tmp[4]))

notset = set()
for i in c:
    tmp = i.strip().split(',')
    notset.add(tmp[0])

for i in ids:
    if i[0] not in notset:
        l.write(i[0]+ ',' + i[1] + '\n')