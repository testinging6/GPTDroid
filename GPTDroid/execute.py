import time
from RunOnEmu.controller import EmuRunner
from UTG.states_and_views import StateViewInfo
from Recommend.util import get_view_refer_name
from RunOnEmu.finishing_operation import FinishOperation
from RunOnEmu.xml_page_analyse import has_scroll_view
from UTG.view import View
from RunOnEmu.util import check_crash



class Executor():
    def __init__(self, controller: EmuRunner, state_view_info: StateViewInfo):
        self.controller = controller
        self.state_view_info = state_view_info
        self.execute_history = {}

    def execute(self, recommend_meta: dict):
        # execute_prj = 1
        need_try_fill = False
        need_try_back = False
        visit_states = {}
        # special_input_map = {"apostrophe": '"', "space": " "}
        recommend_paths = recommend_meta["recommend_paths"]
        input_contents = recommend_meta["input_contents"]
        max_goal = recommend_meta["max_goal"]
        if len(input_contents) > 0:
            input_content = input_contents[0]
            # print("### use input content:", input_content)
            # if input_content in special_input_map.keys():
            #     input_content = special_input_map[input_content]
        else:
            input_content = 'HelloWorld'
        click_view_path = []
        path_hash_key = ""
        finish_goal = 0
        create_count = 0
        has_edittext_to_fill = False
        has_confirm_button = False
        for path_idx, path_info in enumerate(recommend_paths):
            recommend_path = path_info[0]
            click_view_path = recommend_path.view_path
            finish_goal = recommend_path.get_finish_count()
            create_count = len(recommend_path.create_score)
            state_will_fill = set()
            for view_xpath in click_view_path:
                if "_FillInfo" in view_xpath:
                    state_will_fill.add(view_xpath.split("###")[0])
            path_hash_key = recommend_path.get_hash_key()
            for view_key in click_view_path:
                state_id = view_key.split("###")[0]
                state_edittext = self.state_view_info.states[state_id].get_all_edittext()
                for edittext_key in state_edittext:
                    if edittext_key not in click_view_path and state_id not in state_will_fill:
                        has_edittext_to_fill = True
                        break
                cur_view = self.state_view_info.views[view_key]
                if self.state_view_info.check_is_confirm_button(cur_view):
                    has_confirm_button = True
            last_view_key = click_view_path[-1]
            last_view = self.state_view_info.views[last_view_key]
            last_view_name = get_view_refer_name(last_view)
            last_is_search = "search" in last_view_name
            need_try_fill = ((has_confirm_button and has_edittext_to_fill) or last_is_search)
            # need_try_fill = ((has_confirm_button and has_edittext_to_fill) or last_is_search) and len(click_view_path) > 3
            last_view = self.state_view_info.views[click_view_path[-1]]
            need_try_back = get_view_refer_name(last_view) == "ok"
            if path_hash_key not in self.execute_history.keys():
                self.execute_history.setdefault(path_hash_key, 0)
                break
            if self.execute_history[path_hash_key] == 0:
                # print("try path", path_idx, "again!")
                self.execute_history[path_hash_key] = 1
                break
            # if self.execute_history[path_hash_key] == 1 and has_edittext:
            #     print("try path", path_idx, "again, fill all edit text!")
            #     fill_all_edittext = True
            #     break
            else:
                print("path", path_idx, "has try!")
        if len(click_view_path) == 0:
            return "", visit_states
        first_view = click_view_path[0].split(".")[-1]
        if finish_goal == 0 and create_count == 0 and max_goal > 1:
            print("### current best path finish nothing, skip execute")
            return "", visit_states
        path_excute_res = self.excute_click_view_path(click_view_path, False, input_content)
        time.sleep(2)
        if check_crash():
            self.state_view_info.export_crash_steps(click_view_path)
            return path_excute_res["final_state"], visit_states
        if path_excute_res["success"]:
            self.execute_history[path_hash_key] = 1
            final_state = path_excute_res["final_state"]
            visit_states = path_excute_res["visit_states"]
            # if final_state == "state_0" or final_state == "emu_launcher" or check_crash():
            if check_crash():
                self.state_view_info.export_crash_steps(click_view_path)
                return final_state, visit_states
            if need_try_fill:
                print("### try path again, fill all edit text!")
                self.controller.restart_app()
                path_excute_res = self.excute_click_view_path(click_view_path, True, input_content)
                final_state = path_excute_res["final_state"]
                visit_states = path_excute_res["visit_states"]
                return final_state, visit_states
            if need_try_back:
                print("### try path again, back at last step!")
                self.controller.restart_app()
                path_excute_res = self.excute_click_view_path(click_view_path, False, input_content)
                time.sleep(1)
                self.controller.click_back()
                final_state = path_excute_res["final_state"]
                visit_states = path_excute_res["visit_states"]
                return final_state, visit_states
        final_state = path_excute_res["final_state"]
        visit_states = path_excute_res["visit_states"]
        # if final_state == "state_0" or final_state == "emu_launcher" or check_crash():
        if check_crash():
            self.state_view_info.export_crash_steps(click_view_path)
        return final_state, visit_states

    def excute_click_view_path(self, click_view_path, fill_all_edittext, input_content):
        self.wait_restart()
        visit_states = {}
        click_class = [v.split(".")[-1] for v in click_view_path]
        # print("click_class", click_class)
        for click_idx, click_view in enumerate(click_view_path):
            print(click_view)
            view_state = click_view.split("###")[0]
            view_xpath = click_view.split("###")[1]
            cur_state = self.controller.get_current_state()
            visit_states.setdefault(cur_state, 0)
            if view_state != cur_state:
                print("state not match, expect:", view_state, ", get:", cur_state)
                # if cur_state != "unknown":
                #     state_view_info.update_view_transfer(click_view, cur_state)
                #     print("update:", click_view, state_view_info.views[click_view].dst_state)
                transfer_views = self.state_view_info.get_transfer_path(cur_state, view_state)
                print(transfer_views)
                if len(transfer_views) == 0:
                    print(cur_state, "can't reach", view_state)
                    if click_idx + 1 >= len(transfer_views):
                        return {"success": False, "final_state": "", "visit_states": visit_states}
                    next_click_view = click_view_path[click_idx + 1]
                    next_view_cluster = next_click_view.split("###")[0]
                    if cur_state == next_view_cluster:
                        print("pass this step")
                        continue
                    if cur_state != next_view_cluster:
                        print("try transfer from", cur_state, "to", next_view_cluster)
                        transfer_views = self.state_view_info.get_transfer_path(cur_state, next_view_cluster)
                        if len(transfer_views) == 0:
                            # return "", visit_states
                            return {"success": False, "final_state": "", "visit_states": visit_states}
                for (transfer_key, from_state, to_state) in transfer_views:
                    try_time = 0
                    print(transfer_key)
                    while try_time < 3:
                        before_state = self.controller.get_current_state()
                        visit_states.setdefault(before_state, 0)
                        if before_state == from_state:
                            print("start match")
                        if "KEY#" in transfer_key:
                            self.controller.click_back()
                        else:
                            trans_view_xpath = transfer_key.split("###")[1]
                            self.controller.click_view_by_xpath(transfer_key)
                        after_cluster = self.controller.get_current_state()
                        visit_states.setdefault(after_cluster, 0)
                        if after_cluster == to_state:
                            print("transfer done!")
                            if fill_all_edittext:
                                self.controller.detect_edittext_and_fill(input_content)
                            break
                        else:
                            try_time += 1
            if fill_all_edittext:
                self.controller.detect_edittext_and_fill(input_content)
            visit_states.setdefault(view_state, 0)
            if "KEY#" in view_xpath:
                if "back" in view_xpath.lower():
                    print("excute back")
                    back_view = self.state_view_info.views[click_view]
                    print("click back")
                    self.controller.click_back()
                    state_after_click = self.controller.get_current_state()
                    visit_states.setdefault(state_after_click, 0)
                    except_dst_state = back_view.dst_state
                    if except_dst_state != state_after_click and state_after_click == view_state:
                        print("not change, try one more time!")
                        self.controller.click_back()
                        state_after_click = self.controller.get_current_state()
                        visit_states.setdefault(state_after_click, 0)
                        except_dst_state = back_view.dst_state
                    if state_after_click != except_dst_state:
                        print("update1 " + click_view + " dst state")
                        print(
                            "from:" + view_state + "->" + except_dst_state + " to " + view_state + "->" + state_after_click)
                        self.state_view_info.update_view_transfer(click_view, state_after_click)
                        if state_after_click == "state_0":
                            # return "", visit_states
                            return {"success": False, "final_state": "", "visit_states": visit_states}
                        return {"success": False, "final_state": "", "visit_states": visit_states}
                    if state_after_click == "state_0" and not check_crash():
                        relaunch_res = self.controller.relaunch_app()
                        if relaunch_res:
                            state_after_click = self.controller.get_current_state()
                    if check_crash() or state_after_click == "crash_page":
                        # reach desktop
                        print("find crash!")
                        final_state = self.controller.get_current_state()
                        return {"success": True, "final_state": final_state, "visit_states": visit_states}
                elif "rotate" in view_xpath.lower():
                    print("rotate_to_landscape")
                    self.controller.rotate_to_landscape()
                    time.sleep(1)
                    print("rotate_to_landscape check_crash")
                    if check_crash():
                        # reach desktop
                        print("find crash!")
                        final_state = self.controller.get_current_state()
                        return {"success": True, "final_state": final_state, "visit_states": visit_states}
                elif "restart" in view_xpath.lower():
                    print("restart app")
                    self.controller.restart_app(reset=False)
                    time.sleep(2)
                    print("restart app check_crash")
                    if check_crash():
                        # reach desktop
                        print("find crash!")
                        final_state = self.controller.get_current_state()
                        return {"success": True, "final_state": final_state, "visit_states": visit_states}
            else:
                if "_FillInfo" in view_xpath:
                    self.controller.detect_edittext_and_fill(input_content)
                    self.controller.edittext_has_input = set()
                    view_xpath = view_xpath.replace("_FillInfo", "")
                view = self.state_view_info.views[click_view]
                if view.view_class[-8:].lower() == "edittext":
                    print("fill the edittext:", get_view_refer_name(view))
                    self.controller.send_view_text(view_xpath, input_content)
                    if check_crash():
                        # reach desktop
                        print("find crash!")
                        final_state = self.controller.get_current_state()
                        return {"success": True, "final_state": final_state, "visit_states": visit_states}
                else:
                    print("click target_view:", get_view_refer_name(view))
                    excute_res = self.controller.click_view_by_xpath(click_view)
                    state_after_click = self.controller.get_current_state()
                    if not excute_res:
                        print("### Error: can not find target_view")
                        # return "", visit_states
                        return {"success": False, "final_state": "", "visit_states": visit_states}
                    if state_after_click == "state_0" and not check_crash():
                        relaunch_res = self.controller.relaunch_app()
                        if relaunch_res:
                            state_after_click = self.controller.get_current_state()
                    visit_states.setdefault(state_after_click, 0)
                    except_dst_state = view.dst_state
                    dst_state_not_sure = view.dst_state_not_sure
                    if excute_res and state_after_click != except_dst_state and state_after_click != "state_0":
                        print("state_after_click:", state_after_click)
                        print("except_dst_state:", except_dst_state)
                        if not fill_all_edittext:
                            if click_view not in click_view_path[:click_idx]:
                                print("update2 " + click_view + " dst state")
                                print("from:" + view_state + "->" + except_dst_state + " to " + view_state + "->" \
                                      + state_after_click)
                                self.state_view_info.update_view_transfer(click_view, state_after_click)
                        else:
                            ori_view_info = self.state_view_info.views[click_view].to_dict()
                            fill_info_key = click_view + "_FillInfo"
                            fill_info_view = View(ori_view_info)
                            self.state_view_info.views.setdefault(fill_info_key, fill_info_view)
                            self.state_view_info.update_view_transfer(fill_info_key, state_after_click)
                        return {"success": False, "final_state": state_after_click, "visit_states": visit_states}
                    elif state_after_click == except_dst_state and dst_state_not_sure:
                        view.dst_state_not_sure = False
                    if check_crash() or state_after_click == "crash_page":
                        # reach desktop
                        print("find crash!")
                        final_state = self.controller.get_current_state()
                        return {"success": True, "final_state": final_state, "visit_states": visit_states}
                    # if state_after_click == "unknown":
                    #     current_activity, page_source = self.controller.get_page_info()
                    #     new_state_id = self.state_view_info.add_state(current_activity, page_source, click_view, click_view_path)
                    #     print("# find a new state!", new_state_id)
                    #     visit_states.setdefault(new_state_id, 1)
        if fill_all_edittext:
            self.controller.detect_edittext_and_fill(input_content)
        final_state = self.controller.get_current_state()
        # if final_state != "state_0" and final_state != "unknown" and final_state != "emu_launcher":
        #     finish_operator.do_finish_operations()
        #     final_state = self.controller.get_current_state()
        if final_state == "unknown":
            # if "rotate" not in click_view_path[-1].lower() :
            if "rotate" not in click_view_path[-1].lower():
                # current_activity, page_source = self.controller.get_page_info()
                # new_state_id, new_state_xml_path, new_state_img_path = self.state_view_info.get_new_state_name()
                # self.controller.save_screen_img(new_state_img_path)
                # new_state_id = self.state_view_info.add_state(current_activity, page_source, click_view_path[-1],
                #                                               new_state_id, new_state_xml_path, new_state_img_path)
                # # new_state_id = self.state_view_info.add_state(current_activity, page_source, click_view_path[-1])
                # print("# find a new state!", new_state_id)
                current_activity, page_source = self.controller.get_page_info()
                new_state_id, new_state_xml_path, new_state_img_path = self.state_view_info.get_new_state_name()
                self.controller.save_screen_img(new_state_img_path)
                has_find_views = set()
                new_state_id = self.state_view_info.add_state(current_activity, page_source, click_view_path[-1],
                                                              new_state_id, new_state_xml_path, new_state_img_path,
                                                              has_find_views)
                need_scroll = has_scroll_view(page_source)
                if need_scroll:
                    scroll_times = 0
                    while scroll_times < 3:
                        scroll_times += 1
                        self.controller.swipe_down()
                        time.sleep(1)
                        current_activity, page_source = self.controller.get_page_info()
                        self.state_view_info.add_scroll_state(page_source, new_state_id, new_state_img_path,
                                                              has_find_views)
                print("# find a new state:", new_state_id)
                visit_states.setdefault(new_state_id, 1)
        else:
            visit_states.setdefault(final_state, 0)
        # return final_state, visit_states
        return {"success": True, "final_state": final_state, "visit_states": visit_states}

    def wait_restart(self):
        init_state = self.controller.get_current_state()
        while init_state != "state_1":
            time.sleep(2)
            print("waiting restart! current state:", init_state)
            init_state = self.controller.get_current_state()

if __name__ == '__main__':
    # execute()
    pass
