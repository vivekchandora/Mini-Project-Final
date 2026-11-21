from app.services.census_reference import find_census_reference


def test_mumbai_and_pune_census_reference():
    mumbai = find_census_reference("Mumbai, Mumbai City, Maharashtra, India")
    pune = find_census_reference("Pune, Pune City Subdistrict, Maharashtra, India")
    assert mumbai["population"] == 18394912
    assert mumbai["unit_type"] == "Urban Agglomeration"
    assert pune["population"] == 5057709


def test_unknown_city_has_no_fabricated_census_reference():
    assert find_census_reference("Made Up City, India") is None
