-- audit/recon checks for the legacy and refactored table. 
-- Can only run one at a time
{%- set old_relation = ref("customer_orders_legacy") -%}
{%- set dbt_relation = ref("fct_customer_orders") -%}

{{
    audit_helper.compare_relations(
        a_relation=old_relation, b_relation=dbt_relation, primary_key="order_id"
    )
}}

{%- set old_relation = ref("customer_orders_legacy") -%}
{%- set dbt_relation = ref("fct_customer_orders") -%}

{{
    audit_helper.compare_all_columns(
        a_relation=old_relation, b_relation=dbt_relation, primary_key="order_id"
    )
}}