{#
  Emit custom schemas verbatim (staging, intermediate, marts, seeds) instead of dbt's
  default <target_schema>_<custom_schema> concatenation. This keeps the warehouse layout
  readable and matches how the marts are referenced downstream (e.g. marts.mart_revenue_daily).
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
