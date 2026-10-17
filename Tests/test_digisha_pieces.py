"""Une photo ou un document dans la saisie DiGiSha (Patrick, 17.10.2026) : le tour en blocs est admis et borné, son texte
sert au fil et au journal, le point de cache tombe sur le dernier bloc, le résumé de mémoire ne voit jamais les octets."""
import base64
import os
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from routers.digisha import ChatTurn, _cache_history, derniere_question, pieces_du_dernier  # noqa: E402
from routers.digisha_memoire import _rendu  # noqa: E402
from routers.digisha_pieces import texte_de  # noqa: E402

PNG = base64.b64encode(b"\x89PNG petit").decode()
PDF = base64.b64encode(b"%PDF-1.4 petit").decode()


def _img():
    return {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": PNG}}


def test_texte_inchange_pour_les_apps_d_aujourd_hui():
    t = ChatTurn(role="user", content="Céphalée 9/10")
    assert t.content == "Céphalée 9/10" and texte_de(t.content) == "Céphalée 9/10"
    assert _cache_history([{"role": "user", "content": "x"}])[-1]["content"] == [
        {"type": "text", "text": "x", "cache_control": {"type": "ephemeral"}}]


def test_photo_et_document_dans_le_tour():
    t = ChatTurn(role="user", content=[
        {"type": "text", "text": "Voici la photo de ma main"}, _img(),
        {"type": "document", "title": "Résultats", "source": {"type": "base64", "media_type": "application/pdf", "data": PDF}},
    ])
    assert texte_de(t.content) == "Voici la photo de ma main\n[photo]\n[document : Résultats]"
    dump = t.model_dump(exclude_none=True)
    assert dump["content"][1]["source"]["media_type"] == "image/png"
    assert "title" not in dump["content"][1]

    class Corps:
        messages = [t]
    assert derniere_question(Corps) == "Voici la photo de ma main\n[photo]\n[document : Résultats]"
    assert pieces_du_dernier(Corps) == 2


def test_cache_sur_le_dernier_bloc():
    msgs = [{"role": "user", "content": [{"type": "text", "text": "a"}, _img()]}]
    out = _cache_history(msgs)
    assert out[-1]["content"][-1]["cache_control"] == {"type": "ephemeral"}
    assert "cache_control" not in out[-1]["content"][0]
    assert "cache_control" not in msgs[0]["content"][-1]   # l'original intact


def test_types_et_tailles_bornes():
    with pytest.raises(ValidationError):
        ChatTurn(role="user", content=[{"type": "image", "source": {"type": "base64", "media_type": "image/heic", "data": PNG}}])
    with pytest.raises(ValidationError):
        ChatTurn(role="user", content=[{"type": "document", "source": {"type": "base64", "media_type": "text/plain", "data": PDF}}])
    gros = "A" * (5 * 1024 * 1024 * 4 // 3 + 400)
    with pytest.raises(ValidationError):
        ChatTurn(role="user", content=[{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": gros}}])
    with pytest.raises(ValidationError):
        ChatTurn(role="user", content=[_img()] * 5)
    with pytest.raises(ValidationError):
        ChatTurn(role="user", content=[])


def test_le_resume_de_memoire_ne_voit_que_le_texte():
    r = _rendu([{"role": "user", "content": [{"type": "text", "text": "regarde"}, _img()]},
                {"role": "assistant", "content": "Je vois une main."}])
    assert r == "Elle : regarde\n[photo]\n\nDiGiSha : Je vois une main."
    assert PNG not in r
