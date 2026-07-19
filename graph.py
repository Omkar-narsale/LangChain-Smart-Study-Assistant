from chains import build_study_chain

chain = build_study_chain()
print(chain.get_graph().draw_ascii())