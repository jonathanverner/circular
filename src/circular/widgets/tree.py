from lib.template.tag import TagPlugin, TplNode, T_EXPRESSION

class Tree(TagPlugin):
    """
        Usage:

        <w-tree root='project' indent='0.2' click='click_item(child,event)'>
            <tpl-template name='item_view' class='widget w-tree-item'>
                    <span class='widget w-icon {{ child['icon'] }}'></span>
                    <span class='widget w-title'> {{ child['title'] }} </span>
            </tpl-template>
        </w-tree>
    """
    NAME='w-tree'
    TEMPLATE="""
    <ul class='widget w-tree'>
    <li class='widget w-tree-child' tpl-for="child in root[children_attr]">
        <div class='widget w-tree-indented' tpl-style="{'padding-left':depth*indent+'em'}">
            <span class='widget w-tree-indicator w-tree-indicator-{{indicator_class(child)}}' tpl-click='open_tree(child)'></span>
            <tpl-include name='item_view' context="child"></tpl-include>
        </div>
        <div tpl-if="child[children_attr] and opened(child)">
            <widget-tree indent="indent"
                         children_attr="children_attr"
                         root="child[children_attr]"
                         depth="depth+1"
            ></widget-tree>
        </div>
    </li>
    </ul>
    """
    BINDINGS = []

    def __init__(self, node, element, root, click, children_attr='children', indent=0.2):
        super().__init__(node,element)
        pass

TplNode.register_plugin(Tree)