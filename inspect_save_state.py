import pygad

filename = 'genetic_algorithm_results_1'
ga_instance: pygad.GA = pygad.load(filename)

ga_instance.summary()
ga_instance.plot_fitness()
