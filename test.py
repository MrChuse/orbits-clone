import pytest

from pygame import Vector2
from back import Ray, Sphere

@pytest.mark.parametrize("ray, sphere, expected_result", [
    (Ray(origin=Vector2(x=0, y=0), direction=Vector2(x=1, y=0)), Sphere(center=Vector2(x=2, y=0), velocity=Vector2(x=0, y=0), radius=1), 2),
    (Ray(origin=Vector2(x=0, y=0), direction=Vector2(x=1, y=0)), Sphere(center=Vector2(x=-2, y=0), velocity=Vector2(x=0, y=0), radius=1), None),
    (Ray(origin=Vector2(0.331548, 0.424183), direction=Vector2(-0.00496401, 0.000598832)), Sphere(center=Vector2(0.27369, 0.22528), velocity=Vector2(0, 0), radius=0.01864406779661017), None)
])
def test_ray_intersects_sphere(ray: Ray, sphere: Sphere, expected_result):
    assert ray.intersects_sphere(sphere) == expected_result

@pytest.mark.parametrize("ray1, ray2, expected_intersection", [
    # (Ray(Vector2(0, 0), Vector2(1, 0)), Ray(Vector2(1, 0), Vector2(0, -1)), 0.0),  # intersect at distance 1
    # (Ray(Vector2(0, 0), Vector2(0, 1)), Ray(Vector2(0, 1), Vector2(1, 0)), 0.0),  # no intersection
    # (Ray(Vector2(0, 0), Vector2(-1, -1)), Ray(Vector2(1, 1), Vector2(1, 1)), None),  # no intersection
    # (Ray(Vector2(0, 0), Vector2(1, 0)), Ray(Vector2(1, 1), Vector2(0, -1)), 1),  # no intersection
    (Ray(origin=Vector2(142, 203), direction=Vector2(117, -59)), Ray(origin=Vector2(403, 213), direction=Vector2(-62, -24)), 114.37640774044101)
])
def test_calculate_intersection(ray1: Ray, ray2: Ray, expected_intersection):
    assert ray1.intersects(ray2) == expected_intersection