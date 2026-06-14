import random
import math
from typing import List, Dict, Tuple, Any
import numpy as np
from .dynamics import simulator


class GeneticAlgorithmOptimizer:
    def __init__(self):
        self.num_spindles_min = 16
        self.num_spindles_max = 64
        self.blade_angle_min = 15.0
        self.blade_angle_max = 75.0
        self.convergence_history = []

    def initialize_population(self, population_size: int) -> List[Dict[str, Any]]:
        population = []
        for _ in range(population_size):
            individual = {
                "num_spindles": random.randint(self.num_spindles_min, self.num_spindles_max),
                "blade_angle": random.uniform(self.blade_angle_min, self.blade_angle_max)
            }
            population.append(individual)
        return population

    def fitness_function(self, individual: Dict[str, Any], water_speed: float,
                         wheel_radius: float, gear_ratio: float,
                         mechanical_efficiency: float, friction_coefficient: float,
                         min_tension: float, max_tension: float,
                         max_twist_cv: float) -> float:
        num_spindles = individual["num_spindles"]
        blade_angle = individual["blade_angle"]

        result = simulator.simulate(
            water_speed=water_speed,
            blade_angle=blade_angle,
            wheel_radius=wheel_radius,
            gear_ratio=gear_ratio,
            mechanical_efficiency=mechanical_efficiency,
            num_spindles=num_spindles,
            friction_coefficient=friction_coefficient
        )

        spindles = result["spindles"]
        tensions = [s["tension"] for s in spindles if not s["broken"]]

        if not tensions:
            return -1000.0

        tension_valid = all(min_tension <= t <= max_tension for t in tensions)
        twist_cv_valid = result["twist_uniformity_cv"] <= max_twist_cv
        breakage_valid = result["breakage_rate"] <= 5.0

        if not (tension_valid and twist_cv_valid and breakage_valid):
            penalty = 0.0
            if not tension_valid:
                min_t = min(tensions) if tensions else 0
                max_t = max(tensions) if tensions else 0
                penalty += abs(min_t - min_tension) * 10 if min_t < min_tension else 0
                penalty += abs(max_t - max_tension) * 10 if max_t > max_tension else 0
            if not twist_cv_valid:
                penalty += (result["twist_uniformity_cv"] - max_twist_cv) * 50
            if not breakage_valid:
                penalty += (result["breakage_rate"] - 5.0) * 20
            return result["energy_efficiency"] * 0.1 - penalty

        objective = result["energy_efficiency"] * 0.7 + result["total_production_rate"] * 0.3
        return objective

    def selection(self, population: List[Dict[str, Any]],
                  fitness_scores: List[float],
                  num_parents: int) -> List[Dict[str, Any]]:
        indexed_fitness = list(zip(population, fitness_scores))
        indexed_fitness.sort(key=lambda x: x[1], reverse=True)
        parents = [ind for ind, _ in indexed_fitness[:num_parents]]
        return parents

    def tournament_selection(self, population: List[Dict[str, Any]],
                             fitness_scores: List[float],
                             tournament_size: int = 3) -> Dict[str, Any]:
        indices = random.sample(range(len(population)), tournament_size)
        best_idx = max(indices, key=lambda i: fitness_scores[i])
        return population[best_idx]

    def crossover(self, parent1: Dict[str, Any],
                  parent2: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        child1 = {}
        child2 = {}

        if random.random() < 0.5:
            child1["num_spindles"] = parent1["num_spindles"]
            child2["num_spindles"] = parent2["num_spindles"]
        else:
            child1["num_spindles"] = parent2["num_spindles"]
            child2["num_spindles"] = parent1["num_spindles"]

        alpha = random.random()
        child1["blade_angle"] = alpha * parent1["blade_angle"] + (1 - alpha) * parent2["blade_angle"]
        child2["blade_angle"] = (1 - alpha) * parent1["blade_angle"] + alpha * parent2["blade_angle"]

        return child1, child2

    def mutate(self, individual: Dict[str, Any], mutation_rate: float = 0.1) -> Dict[str, Any]:
        mutated = dict(individual)

        if random.random() < mutation_rate:
            mutation_amount = random.randint(-5, 5)
            mutated["num_spindles"] = max(
                self.num_spindles_min,
                min(self.num_spindles_max, mutated["num_spindles"] + mutation_amount)
            )

        if random.random() < mutation_rate:
            mutation_amount = random.uniform(-5.0, 5.0)
            mutated["blade_angle"] = max(
                self.blade_angle_min,
                min(self.blade_angle_max, mutated["blade_angle"] + mutation_amount)
            )

        return mutated

    def optimize(self, water_speed: float, wheel_radius: float,
                 gear_ratio: float, mechanical_efficiency: float,
                 friction_coefficient: float, min_tension: float,
                 max_tension: float, max_twist_cv: float,
                 population_size: int = 50, generations: int = 100) -> Dict[str, Any]:
        population = self.initialize_population(population_size)
        self.convergence_history = []
        best_fitness_all = float('-inf')
        best_individual_all = None

        for generation in range(generations):
            fitness_scores = [
                self.fitness_function(
                    ind, water_speed, wheel_radius, gear_ratio,
                    mechanical_efficiency, friction_coefficient,
                    min_tension, max_tension, max_twist_cv
                )
                for ind in population
            ]

            best_fitness = max(fitness_scores)
            self.convergence_history.append(best_fitness)

            if best_fitness > best_fitness_all:
                best_fitness_all = best_fitness
                best_idx = fitness_scores.index(best_fitness)
                best_individual_all = dict(population[best_idx])

            num_parents = population_size // 2
            parents = self.selection(population, fitness_scores, num_parents)

            new_population = []

            while len(new_population) < population_size:
                parent1 = self.tournament_selection(population, fitness_scores)
                parent2 = self.tournament_selection(population, fitness_scores)
                child1, child2 = self.crossover(parent1, parent2)
                child1 = self.mutate(child1, mutation_rate=0.15)
                child2 = self.mutate(child2, mutation_rate=0.15)
                new_population.append(child1)
                if len(new_population) < population_size:
                    new_population.append(child2)

            if best_individual_all:
                new_population[0] = dict(best_individual_all)

            population = new_population

        final_result = simulator.simulate(
            water_speed=water_speed,
            blade_angle=best_individual_all["blade_angle"],
            wheel_radius=wheel_radius,
            gear_ratio=gear_ratio,
            mechanical_efficiency=mechanical_efficiency,
            num_spindles=best_individual_all["num_spindles"],
            friction_coefficient=friction_coefficient
        )

        return {
            "optimal_num_spindles": best_individual_all["num_spindles"],
            "optimal_blade_angle": round(best_individual_all["blade_angle"], 2),
            "max_objective_value": best_fitness_all,
            "total_production_rate": final_result["total_production_rate"],
            "energy_efficiency": final_result["energy_efficiency"],
            "twist_uniformity_cv": final_result["twist_uniformity_cv"],
            "breakage_rate": final_result["breakage_rate"],
            "convergence_history": self.convergence_history
        }


optimizer = GeneticAlgorithmOptimizer()
