Welcome to your new dbt project!

# Using the starter project

Try running the following commands:
- dbt run
- dbt test


# Resources:
- Learn more about dbt [in the docs](https://docs.getdbt.com/docs/introduction)
- Check out [Discourse](https://discourse.getdbt.com/) for commonly asked questions and answers
- Join the [dbt community](https://getdbt.com/community) to learn from other analytics engineers
- Find [dbt events](https://events.getdbt.com) near you
- Check out [the blog](https://blog.getdbt.com/) for the latest news on dbt's development and best practices


# Notes

## codegen

Tool for auto generating code within dbt

- [Official docs](https://hub.getdbt.com/dbt-labs/codegen/latest/)
- [Github](https://github.com/dbt-labs/dbt-codegen/tree/0.14.1/#generate_source-source)
    
## Tests


```bash
dbt test # run all generic and singular tests in your project.
dbt test --select test_type:generic # run only generic tests in your project.
dbt test --select test_type:singular # run only singular tests in your project.
```

### Generic

Simple generic prebuilt tests. Come in 4 flavors. Live in the models.yaml file

- Unique - The values are unique
- Not NUll - the values are not null
- Accepted Values - the values are in an accepted list of values
- Relationships - No orphaned keys between tables

### Custom Tests (Singular Tests)

- Custom built tests via sql query file. Supports jinja
- lives in the src folder.
- Recommend mirroring the src folder layout to keep tests simple.