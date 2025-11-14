from srcs.dq.agent import call_agent


def create_prompt(source_features: list[str]) -> str:
    return f"""
<task>
    You must determine whether a target feature logically corresponds to any feature from the given list.
    You will receive the target feature description separately.
    If a match exists, output the exact source feature name.
    If no match exists, output exactly: NAN.
</task>

<rules>
    <rule>Respond with only one token: a feature name from the list OR NAN.</rule>
    <rule>No explanations, no comments, no reasoning.</rule>
    <rule>No punctuation or extra text.</rule>
    <rule>Decision must be based ONLY on the provided target feature description.</rule>
</rules>

<input>
    {{TARGET_BLOCK}}

    <source_features>
        {''.join(f'<feature>{sf}</feature>' for sf in source_features)}
    </source_features>
</input>

<output>
    <!-- Write ONLY: matched feature name OR NAN -->
</output>
"""


def create_user_message(target_feature: str, target_feature_values) -> str:
    return f"""
<target_feature>
    <name>{target_feature}</name>
    <values>{target_feature_values}</values>
</target_feature>
"""


def map_feature(target_feature: str, target_feature_values, source_features: list[str]):
    prompt = create_prompt(source_features)
    user_message = create_user_message(target_feature, target_feature_values)
    result = call_agent(prompt, user_message)
    return result


# res = map_feature(target_feature="CustomerAge", target_feature_values=[21, 35, 44], source_features=["age", "height", "income"])
# print(res)
