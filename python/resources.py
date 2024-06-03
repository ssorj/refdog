from common import *

def generate():
    debug("Generating resources")

    make_dir("input/resources")

    model = ResourceModel()
    lines = list()

    def append(line=""):
        if line is None:
            return

        lines.append(line)

    append("# Skupper resources")
    append()

    for group in model.groups:
        # append(f"- [{group.name}](#{group.id})")
        append(f"- {group.name}")

        for resource in group.resources:
            append(f"  - [{resource.name}]({resource.id}.html)")

    write("input/resources/index.md", "\n".join(lines))

    for group in model.groups:
        for resource in group.resources:
            generate_resource(resource)

def generate_resource(resource):
    debug(f"Generating {resource}")

    lines = list()

    def append(line=""):
        if line is None:
            return

        lines.append(line)

    append("---")
    append("body_class: resource")
    append("---")
    append()
    append(f"# {resource.name}")
    append()
    append("<section>")
    append()

    if resource.description:
        append(resource.description.strip())
        append()

    if resource.links:
        links = ["[{}]({{{{site_prefix}}}}{})".format(x["name"], x["url"]) for x in resource.links]
        append("_See also:_ " + ", ".join(links))
        append()

    append("</section>")
    append()

    if resource.examples:
        append("<section>")
        append()
        append("## Examples")
        append()

        for example in resource.examples:
            # XXX An example object
            append(example["description"].strip() + ":")
            append()
            append("~~~ yaml")
            append(example["yaml"].strip())
            append("~~~")
            append()

        append("</section>")
        append()

    if resource.spec_properties:
        append("<section>")
        append()
        append("## Spec properties")
        append()

        for prop in resource.spec_properties:
            generate_property(prop, append)

        append("</section>")
        append()

    if resource.status_properties:
        append("<section>")
        append()
        append("## Status properties")
        append()

        for prop in resource.status_properties:
            generate_property(prop, append)

        append("</section>")
        append()

    write(f"input/resources/{resource.id}.md", "\n".join(lines))

def generate_property(prop, append):
    debug(f"Generating {prop}")

    name = nvl(prop.rename, prop.name)
    id_ = fragment_id(name)
    prop_info = prop.type

    if prop.format:
        prop_info += f" ({prop.format})"

    if prop.required and prop.default is None:
        prop_info += ", required"

    append(f"- <h3 id=\"{id_}\">{name} <span class=\"property-info\">{prop_info}</span></h3>")
    append()

    if prop.description:
        description = "\n".join(f"  {line}" for line in prop.description.strip().split("\n"))

        append(description)
        append()

    if prop.default not in (None, False):
        default = prop.default

        if prop.default is True:
            default = str(prop.default).lower()

        append(f"  _Default:_ {default}")
        append()

    if prop.choices:
        append(f"  _Choices:_")

        for choice in prop.choices:
            append(f"    - `{choice['name']}` - {choice['description']}".rstrip())

        append()

    if prop.links:
        links = ["[{}]({{{{site_prefix}}}}{})".format(x["name"], x["url"]) for x in prop.links]
        append("  _See also:_ " + ", ".join(links))
        append()

    if prop.notes:
        notes = "\n".join(f"  _{line}_" for line in prop.notes.strip().split("\n") if line != "")

        append(notes)
        append()

    # append(f"_Type:_ {capitalize(prop.type)}\\")
    # append(f"_Required:_ {'Yes' if prop.required else 'No'}\\")
    # append(f"_Default:_ {'False' if prop.default is None and prop.type == 'boolean' else prop.default}")

class ResourceModel:
    def __init__(self):
        debug(f"Loading {self}")

        self.data = read_yaml("config/resources.yaml")

        self.groups = list()
        self.resources_by_name = dict()
        self.crds_by_name = dict()

        for group_data in self.data["groups"]:
            self.groups.append(Group(self, group_data))

        for group in self.groups:
            for resource in group.resources:
                self.resources_by_name[resource.name] = resource

        with working_dir("crds"):
            for crd_file in list_dir():
                if crd_file == "skupper_cluster_policy_crd.yaml":
                    continue

                crd_data = read_yaml(crd_file)

                if crd_data["kind"] != "CustomResourceDefinition":
                    continue

                kind = crd_data["spec"]["names"]["kind"]

                self.crds_by_name[kind] = crd_data

        self.check_properties()

    def __repr__(self):
        return "resource model"

    def check_properties(self):
        for crd_name, crd_data in self.crds_by_name.items():
            if crd_name not in self.resources_by_name:
                print(f"Missing: resource '{crd_name}'")

            resource = self.resources_by_name[crd_name]

            for name, data in crd_data["spec"]["versions"][0]["schema"]["openAPIV3Schema"]["properties"]["spec"]["properties"].items():
                if name not in resource.spec_properties_by_name:
                    print(f"Missing: {resource}: {name}")

            for name, data in crd_data["spec"]["versions"][0]["schema"]["openAPIV3Schema"]["properties"]["status"]["properties"].items():
                if name not in resource.status_properties_by_name:
                    print(f"Missing: {resource}: {name}")

    def get_schema(self, resource):
        crd = self.crds_by_name[resource.name]

        try:
            return crd["spec"]["versions"][0]["schema"]["openAPIV3Schema"]
        except KeyError:
            return {}

    def get_schema_property(self, prop):
        schema = self.get_schema(prop.resource)

        try:
            return schema["properties"][prop.group]["properties"][prop.name]
        except KeyError:
            return {}

class Group:
    def __init__(self, model, data):
        self.model = model
        self.data = data

        debug(f"Loading {self}")

        self.resources = list()

        for resource_data in self.data.get("resources", []):
            self.resources.append(Resource(self.model, self, resource_data))

    def __repr__(self):
        return f"group '{self.name}'"

    @property
    def id(self):
        return fragment_id(self.name)

    @property
    def name(self):
        return self.data["name"]

    @property
    def description(self):
        return self.data.get("description")

class Resource:
    def __init__(self, model, group, data):
        self.model = model
        self.group = group
        self.data = data

        debug(f"Loading {self}")

        self.spec_properties = list()
        self.spec_properties_by_name = dict()

        for property_data in self.data.get("spec_properties", []):
            prop = Property(self.model, self, "spec", property_data)

            self.spec_properties.append(prop)
            self.spec_properties_by_name[prop.name] = prop

        self.status_properties = list()
        self.status_properties_by_name = dict()

        for property_data in self.data.get("status_properties", []):
            prop = Property(self.model, self, "status", property_data)

            self.status_properties.append(prop)
            self.status_properties_by_name[prop.name] = prop

    def __repr__(self):
        return f"resource '{self.name}'"

    @property
    def name(self):
        return self.data["name"]

    @property
    def id(self):
        return fragment_id(self.name)

    @property
    def description(self):
        # XXX Default to CRD description
        return self.data.get("description")

    @property
    def links(self):
        return self.data.get("links", [])

    @property
    def examples(self):
        return self.data.get("examples", [])

class Property:
    def __init__(self, model, resource, group, data):
        self.model = model
        self.resource = resource
        self.group = group # "spec" or "status"
        self.data = data

        debug(f"Loading {self}")

    def __repr__(self):
        return f"property '{self.name}'"

    @property
    def name(self):
        return self.data["name"]

    @property
    def rename(self):
        return self.data.get("rename")

    @property
    def type(self):
        default = self.model.get_schema_property(self).get("type")
        return self.data.get("type", default)

    @property
    def format(self):
        default = self.model.get_schema_property(self).get("format")
        return self.data.get("format", default)

    @property
    def required(self):
        schema = self.model.get_schema(self.resource)
        required_names = schema["properties"][self.group].get("required", [])
        default = self.name in required_names

        return self.data.get("required", default)

    @property
    def description(self):
        default = self.model.get_schema_property(self).get("description")
        return self.data.get("description", default)

    @property
    def links(self):
        return self.data.get("links", [])

    @property
    def default(self):
        default = False if self.type == "boolean" else None
        return self.data.get("default", default)

    @property
    def choices(self):
        return self.data.get("choices", [])

    @property
    def notes(self):
        return self.data.get("notes")
