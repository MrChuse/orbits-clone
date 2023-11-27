import pytest

from pygame import Vector2
from back import Ray, Sphere, ray_intersects_sphere


@pytest.mark.parametrize("ray, sphere, expected_result", [
    (Ray(origin=Vector2(x=0, y=0), direction=Vector2(x=1, y=0)), Sphere(center=Vector2(x=2, y=0), velocity=Vector2(x=0, y=0), radius=1), (True, 2)),
    (Ray(origin=Vector2(x=0, y=0), direction=Vector2(x=1, y=0)), Sphere(center=Vector2(x=-2, y=0), velocity=Vector2(x=0, y=0), radius=1), (False, None)),
    (Ray(origin=Vector2(0.331548, 0.424183), direction=Vector2(-0.00496401, 0.000598832)), Sphere(center=Vector2(0.27369, 0.22528), velocity=Vector2(0, 0), radius=0.01864406779661017), (False, None))
])
def test_ray_intersects_sphere(ray, sphere, expected_result):
    assert ray_intersects_sphere(ray, sphere) == expected_result