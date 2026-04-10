import pytest
from app.services.skill_taxonomy import SkillTaxonomyService


@pytest.fixture
def taxonomy():
    return SkillTaxonomyService()


def test_normalize_exact_match(taxonomy):
    """Test exact skill name normalization."""
    canonical, confidence = taxonomy.normalize_skill("Python")
    assert canonical == "Python"
    assert confidence == 1.0


def test_normalize_alias(taxonomy):
    """Test alias normalization."""
    canonical, confidence = taxonomy.normalize_skill("JS")
    assert canonical == "JavaScript"
    assert confidence == 1.0


def test_normalize_case_insensitive(taxonomy):
    """Test case-insensitive normalization."""
    canonical, confidence = taxonomy.normalize_skill("react")
    assert canonical == "React"
    assert confidence == 1.0


def test_normalize_k8s(taxonomy):
    """Test K8s -> Kubernetes normalization."""
    canonical, confidence = taxonomy.normalize_skill("K8s")
    assert canonical == "Kubernetes"
    assert confidence == 1.0


def test_normalize_unknown_skill(taxonomy):
    """Test unknown skill returns low confidence."""
    canonical, confidence = taxonomy.normalize_skill("SomeUnknownFramework2024")
    assert confidence <= 0.5


def test_skill_info(taxonomy):
    """Test getting skill information."""
    info = taxonomy.get_skill_info("Python")
    assert info is not None
    assert info["name"] == "Python"
    assert "category" in info


def test_infer_skills(taxonomy):
    """Test skill inference from combinations."""
    skills = ["TensorFlow", "PyTorch"]
    inferred = taxonomy.infer_skills(skills)
    # Should infer Deep Learning from TensorFlow + PyTorch
    inferred_names = [i["name"] for i in inferred]
    assert "Deep Learning" in inferred_names


def test_search_skills(taxonomy):
    """Test skill search."""
    results = taxonomy.search_skills("python")
    assert len(results) > 0
    assert any(r["name"] == "Python" for r in results)


def test_proficiency_estimation(taxonomy):
    """Test proficiency level estimation."""
    assert taxonomy.estimate_proficiency("Python", years=6) == "expert"
    assert taxonomy.estimate_proficiency("Python", years=3) == "advanced"
    assert taxonomy.estimate_proficiency("Python", years=1) == "intermediate"
    assert taxonomy.estimate_proficiency("Python", years=0.5) == "beginner"


def test_taxonomy_tree(taxonomy):
    """Test full taxonomy tree."""
    tree = taxonomy.get_taxonomy_tree()
    assert "Technical Skills" in tree
    assert "Programming Languages" in tree["Technical Skills"]
