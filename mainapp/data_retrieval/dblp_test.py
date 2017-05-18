import dblp

# x = dblp.search_publication('evolution', range(2010, 2017))
# for author in x:
#     print(author)


author = dblp.search_author("Dariusz Król")
for x in author:
    print(x.data)
