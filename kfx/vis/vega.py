"""Functions to help generate Vega or Vega-Lite spec as web-app in kubeflow pipeline UI."""
import json

from typing import Any

import kfx.dsl
import kfx.vis.models

from kfx.vis._helpers import web_app


def _vega_embed_html(
    spec: dict,
    opts: dict = None,
    title="Generated by kfx.vis",
    vega: int = 5,
    vega_lite: int = 4,
) -> str:
    """Returns a html that generates a Vega or Vega-Lite visualization.

    Args:
        spec (dict): Vega or Vega-Lite spec as a dict.
        opts (dict, optional): Options to pass to vega-embed. Defaults to None.
        title (str, optional): Title for the web app. Defaults to "Generated by kfx.vis".
        vega (int, optional): Major version of Vega to use. Defaults to 5.
        vega_lite (int, optional): Major version of Vega-Lite to use. Defaults to 4.
    """

    return f"""
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/vega@{vega}"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-lite@{vega_lite}"></script>
  <!-- Import vega-embed -->
  <script src="https://cdn.jsdelivr.net/npm/vega-embed@4"></script>
  <title>{title}</title>
  <style>
    html, body {{
      width: 100%;
      height: 100%;
      margin: 0px;
      border: 0;
    }}
    #vis {{
      width: 100%;
      height: 100%;
    }}
    </style>
</head>
<body>

<div id="vis"></div>

<script type="text/javascript">
  var spec = {json.dumps(spec)};
  var opts = {json.dumps(opts or {})}
  vegaEmbed('#vis', spec, opts).then(function(result) {{
    console.log("Generated with kfx.vis (https://github.com/e2fyi/kfx)!")
  }}).catch(console.error);
</script>
</body>
</html>
"""


def _kfp_ui_api(kfp_artifact: kfx.dsl.KfpArtifact) -> str:
    """Returns the path to call to retrieve the artifact.

    Args:
        kfp_artifact ([kfx.dsl.KfpArtifact]): kubflow flow pipeline artifact.

    Returns:
        str: path to the api to get the artifact.
    """
    return f"artifacts/get?source={kfp_artifact.source}&bucket={kfp_artifact.bucket}&key={kfp_artifact.key}"


def _kfp_artifact_to_api(obj: Any) -> Any:
    """Converts any KfpArtifact in a dict into a url to kfp UI api call."""

    if isinstance(obj, kfx.dsl.KfpArtifact):
        return _kfp_ui_api(obj)

    if isinstance(obj, dict):
        return {
            key: _kfp_artifact_to_api(value)
            if isinstance(value, kfx.dsl.KfpArtifact)
            else value
            for key, value in obj.items()
        }

    if isinstance(obj, list):
        return [_kfp_artifact_to_api(item) for item in obj]

    return obj


def vega_web_app(
    spec: dict,
    opts: dict = None,
    title="Generated by kfx.vis",
    vega: int = 5,
    vega_lite: int = 4,
) -> kfx.vis.models.WebApp:
    """Provides the metadata needed for kubeflow pipeline UI to render a `Vega <https://vega.github.io/>`_ or `Vega-Lite <https://vega.github.io/vega-lite/>`_ vis in as a custom web app.

    This web app uses `vega embed <https://github.com/vega/vega-embed>`_ to render the vis.

    Args:
        spec (dict): Vega or Vega-Lite spec as a dict.
        opts (dict, optional): Options to pass to vega-embed. Defaults to None.
        title (str, optional): Title for the web app. Defaults to "Generated by kfx.vis".
        vega (int, optional): Version of Vega to use. Defaults to 5.
        vega_lite (int, optional): Version of Vega-Lite to use. Defaults to 4.

    Returns:
        kfx.vis.models.WebApp: pydantic data object describing a Vega/Vega-Lite web app.
    """
    # so that credential cookies will also be sent
    opts = opts or {}
    opts["loader"] = opts.get("loader", {})
    opts["loader"]["http"] = opts["loader"].get("http", {})
    opts["loader"]["http"].update({"credentials": "same-origin"})

    data = spec.get("data")
    if data:
        # converts any KfpArtifact into api call url
        spec["data"] = _kfp_artifact_to_api(data)

    return web_app(
        source=_vega_embed_html(spec, opts, title, vega=vega, vega_lite=vega_lite),
        storage="inline",
    )
