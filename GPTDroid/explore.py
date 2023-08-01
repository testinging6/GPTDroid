from UTG.states_and_views import StateViewInfo
from Recommend.cal_sim_heuristicly import get_view_sim
# from RunOnEmu.execute import execute
import os
import time
from RunOnEmu.controller import EmuRunner
from RunOnEmu.util import get_recdroid_apk_info, check_crash
import time
import Levenshtein
from Recommend.util import get_view_refer_name
import re
from RunOnEmu.xml_page_analyse import has_scroll_view



class Explorer():
    def __init__(self, controller: EmuRunner, state_view_info: StateViewInfo, match_meta: dict, visit_states: dict,
                 recommend_meta: dict):
        # self.views_need_explore = views_need_explore
        self.views_need_explore = {}
        self.recommend_meta = recommend_meta
        self.controller = controller
        self.state_view_info = state_view_info
        self.match_meta = match_meta
        self.visit_states = visit_states
        self.init_views_need_explore()

    def init_views_need_explore(self):
        new_states = []
        if len(self.state_view_info.new_find_state) > 0:
            new_states = self.state_view_info.new_find_state.copy()

        # temp_not_sure = self.state_view_info.get_dst_state_not_sure_views()

        temp_fill_info_views = {}
        temp_not_sure = {}
        temp_new_views = {}
        temp_on_path_views = {}
        temp_not_sure_relevant_match = {}
        temp_views_relevant_match = {}
        path_state = set()
        state_relevant_match = set()
        self.all_match_need_explore = set()
        match_dst_state = set()
        match_src_state = set()
        match_view2step = self.match_meta["match_view2step"]
        match_need_explore = self.match_meta["match_need_explore"]
        for view_key in match_view2step.keys():
            if "KEY#ROTATE" in view_key:
                continue
            if "KEY#" not in view_key:
                state_relevant_match.add(view_key.split("###")[0])
            cur_src_state = self.state_view_info.views[view_key].src_state
            cur_dst_state = self.state_view_info.views[view_key].dst_state
            if "state" in cur_src_state:
                match_src_state.add(cur_src_state)
            if "state" in cur_dst_state:
                match_dst_state.add(cur_dst_state)
        for state, match_need_explore_views in match_need_explore.items():
            state_relevant_match.add(state)
            for match_need_explore_view in match_need_explore_views:
                if "KEY#ROTATE" in match_need_explore_view:
                    continue
                self.all_match_need_explore.add(match_need_explore_view)
                cur_src_state = self.state_view_info.views[match_need_explore_view].src_state
                cur_dst_state = self.state_view_info.views[match_need_explore_view].dst_state
                if "state" in cur_src_state:
                    match_src_state.add(cur_src_state)
                if "state" in cur_dst_state:
                    match_dst_state.add(cur_dst_state)
        relevant_states = self.state_view_info.get_relevant_states(state_relevant_match)
        need_to_clean_states, self.sure_states = self.get_not_sure_need_to_clean(relevant_states)
        # print("match_need_explore", match_need_explore)
        # print("all_match_need_explore", match_need_explore)
        # print("state_have_match_views", state_relevant_match)
        # print("relevant_states", relevant_states)
        # print("need_to_clean_states", need_to_clean_states)
        # print("sure_states", self.sure_states)
        # print("match_dst_state", match_dst_state)
        for view_key in self.match_meta["match_view2step"].keys():
            view = self.state_view_info.views[view_key]
            src_state = view.src_state
            dst_state = view.dst_state
            path_state.add(src_state)
            path_state.add(dst_state)
        for view_key, view in self.state_view_info.views.items():
            src_state = view.src_state
            dst_state = view.dst_state
            dst_state_not_sure = view.dst_state_not_sure
            explore_flag1 = dst_state == "unknown" or (dst_state == "state_0" and "KEY#" not in view_key)
            explore_flag2 = ("state" in dst_state and dst_state_not_sure)
            transfer_step = len(self.state_view_info.get_transfer_path("state_1", src_state))
            if not (explore_flag1 or explore_flag2):
                continue
            if src_state != "state_1" and transfer_step == 0:
                # print("unreachable:", src_state)
                continue
            if explore_flag1 or explore_flag2 or "_FillInfo" in view_key:
                if explore_flag1:
                    urgent_flag1 = view_key in self.all_match_need_explore and "KEY#ROTATE" not in view_key
                    urgent_flag2 = "_FillInfo" in view_key and src_state in relevant_states
                    if src_state in match_dst_state:
                        # urgent_flag3 = src_state not in match_need_explore.keys()
                        urgent_flag3 = src_state not in match_src_state and src_state != "state_1"
                    else:
                        urgent_flag3 = False
                    if src_state in self.state_view_info.new_find_state:
                        # urgent_flag4 = src_state not in match_need_explore.keys()
                        urgent_flag4 = src_state in match_dst_state
                    else:
                        urgent_flag4 = False
                    if urgent_flag1 or urgent_flag2 or urgent_flag3 or urgent_flag4:
                        # print(urgent_flag1, urgent_flag2, urgent_flag3, urgent_flag4)
                        if src_state not in temp_views_relevant_match.keys():
                            temp_views_relevant_match.setdefault(src_state, set())
                        temp_views_relevant_match[src_state].add(view_key)
                if explore_flag2:
                    urgent_flag1 = src_state in need_to_clean_states
                    urgent_flag2 = view_key in match_view2step.keys()
                    urgent_flag3 = "_FillInfo" in view_key and src_state in relevant_states
                    if urgent_flag1 or urgent_flag2 or urgent_flag3:
                        if src_state not in temp_views_relevant_match.keys():
                            temp_views_relevant_match.setdefault(src_state, set())
                        temp_views_relevant_match[src_state].add(view_key)

            if explore_flag2 or "_FillInfo" in view_key:
                if src_state not in temp_not_sure.keys():
                    temp_not_sure.setdefault(src_state, set())
                temp_not_sure[src_state].add(view_key)
                if src_state in relevant_states:
                    if src_state not in temp_not_sure_relevant_match.keys():
                        temp_not_sure_relevant_match.setdefault(src_state, set())
                    temp_not_sure_relevant_match[src_state].add(view_key)
            if "_FillInfo" in view_key:
                if src_state not in temp_fill_info_views.keys():
                    temp_fill_info_views.setdefault(src_state, set())
                temp_fill_info_views[src_state].add(view_key)
            if src_state in new_states:
                if src_state not in temp_new_views.keys():
                    temp_new_views.setdefault(src_state, set())
                temp_new_views[src_state].add(view_key)
            if src_state in path_state:
                if src_state not in temp_on_path_views.keys():
                    temp_on_path_views.setdefault(src_state, set())
                temp_on_path_views[src_state].add(view_key)
            # if src_state in self.visit_states.keys():
            #     if src_state not in temp_visit_views.keys():
            #         temp_visit_views.setdefault(src_state, set())
            #     temp_visit_views[src_state].add(view_key)

        if len(temp_views_relevant_match.keys()) > 0:
            print("Explore Priority 0: temp_views_relevant_match")
            self.views_need_explore = temp_views_relevant_match
            return

        if len(temp_new_views.keys()) > 0:
            print("Explore Priority 1: explore views in new founded state, but dst state unknown")
            self.views_need_explore = temp_new_views
            self.state_view_info.new_find_state = []
            return

        if len(temp_fill_info_views.keys()) > 0:
            print("Explore Priority 2: explore fill info views")
            self.views_need_explore = temp_fill_info_views
            return

        # if len(temp_not_sure.keys()) > 0:
        #     print("Explore Priority 3: clean all not sure view")
        #     self.views_need_explore = temp_not_sure
        #     return

        if len(temp_on_path_views.keys()) > 0:
            print("Explore Priority 4: explore views that path")
            self.views_need_explore = temp_on_path_views
            return

        # if len(temp_not_sure_relevant_match.keys()) > 0:
        #     print("Explore Priority 1: clean not sure views on states which have match views")
        #     self.views_need_explore = temp_not_sure_relevant_match
        #     return

        # if len(temp_visit_views.keys()) > 0:
        #     print("Explore Priority 4: explore all views that visit state is unknown")
        #     self.views_need_explore = temp_visit_views
        #     return
        # Priority 5: explore all views that dst state is unknown
        print("Explore Priority 5: explore all views that dst state is unknown")
        self.views_need_explore = self.state_view_info.get_views_need_explore()
        return

    def explore_view(self):
        self.wait_restart()
        input_contents = self.recommend_meta["input_contents"]
        if len(input_contents) > 0:
            input_content = input_contents[0]
            # print("### use input content:", input_content)
            # if input_content in special_input_map.keys():
            #     input_content = special_input_map[input_content]
        else:
            input_content = 'HelloWorld'

        all_explore_views = []
        min_transfer_step = 99
        has_match_need_explore = False
        for src_state, view_keys in self.views_need_explore.items():
            if src_state == "state_1":
                transfer_step = 0
            else:
                transfer_step = len(self.state_view_info.get_transfer_path("state_1", src_state))
                if transfer_step == 0:
                    transfer_step = 99999
            if transfer_step < min_transfer_step:
                min_transfer_step = transfer_step
            for view_key in view_keys:
                cur_view = self.state_view_info.views[view_key]
                cur_view_type = cur_view.view_type
                refer_name = get_view_refer_name(cur_view)
                first_flag1 = view_key in self.all_match_need_explore
                first_flag2 = "_FillInfo" in view_key and transfer_step <= min_transfer_step + 2
                # if "_FillInfo" in view_key in view_key:
                #     print("%%% ", view_key, "first_flag2", first_flag2)
                first_flag = (first_flag1 or first_flag2) and src_state in self.sure_states
                # first_flag = (first_flag1 or first_flag2)
                if first_flag:
                    if first_flag1 and first_flag2:
                        cur_transfer_step = 0.1
                    elif first_flag1:
                        has_match_need_explore = True
                        cur_transfer_step = 0.2
                    else:
                        cur_transfer_step = 0.3
                    if "_LongClick" in view_key:
                        cur_transfer_step += 0.05
                    # if cur_transfer_step < min_transfer_step:
                    #     min_transfer_step = cur_transfer_step
                    # print("%%% ", view_key, cur_transfer_step)
                    all_explore_views.append([view_key, cur_transfer_step])
                else:
                    new_transfer_step = transfer_step
                    has_key_word = False
                    # process_words = ["new", "create", "add", "setting", "preference", "option", "next", "start",
                    #                  "study", "ok", "general", "agree", "attach", "enter", "show"]
                    process_words = ["new", "create", "add", "setting", "preference", "option", "next", "start",
                                     "study", "ok", "general", "agree", "attach", "enter", "show"]
                    for process_word in process_words:
                        if process_word in refer_name:
                            has_key_word = True
                            break
                    if has_key_word:
                        new_transfer_step = new_transfer_step - 1
                    if cur_view_type in ["checkbox"] and not has_key_word:
                        new_transfer_step = new_transfer_step + 2
                    if "rotate" in refer_name:
                        new_transfer_step = new_transfer_step + 999
                    if "_LongClick" in view_key:
                        new_transfer_step = new_transfer_step + 0.5
                    if "no password" in refer_name:
                        new_transfer_step = new_transfer_step + 0.5
                    if "_Scroll" in refer_name:
                        new_transfer_step = new_transfer_step + 0.5
                    if "_FillInfo" in view_key:
                        new_transfer_step = new_transfer_step - 1
                    all_explore_views.append([view_key, new_transfer_step])
        all_explore_views.sort(key=lambda x: x[1])
        if len(all_explore_views) == 0:
            self.controller.restart_app()
            return
        if has_match_need_explore:
            min_transfer_step = all_explore_views[0][1]
            explore_range = min_transfer_step + 1
        else:
            explore_range = min_transfer_step + 2
        all_explore_views = [t for t in all_explore_views if t[1] <= explore_range]
        all_explore_views = all_explore_views[:10]
        print("all views need explore:", len(all_explore_views))
        for (view_key, transfer_step) in all_explore_views:
            target_view = self.state_view_info.views[view_key]
            target_refer_name = get_view_refer_name(target_view)
            target_bounds = target_view.bounds
            print("### target:", target_refer_name, target_bounds, view_key.split("###")[0], view_key.split("/")[-1])
            # print(view_key)
            src_state = view_key.split("###")[0]
            # self.wait_restart()
            cur_state = self.controller.get_current_state()
            if cur_state != src_state:
                if cur_state != "state_0" and "state" in cur_state:
                    cur_to_dst_transfer = self.state_view_info.get_transfer_path(cur_state, src_state)
                else:
                    cur_to_dst_transfer = []
                if len(cur_to_dst_transfer) != 0:
                    print("# transfer from cur state")
                    transfer_res = self.transfer_to_src_state(src_state, input_content)
                    if not transfer_res:
                        print("### Error: transfer wrong, skip")
                        continue
                else:
                    start_to_dst_transfer = self.state_view_info.get_transfer_path("state_1", src_state)
                    if len(start_to_dst_transfer) != 0:
                        print("# transfer from state_1")
                        self.wait_restart()
                        transfer_res = self.transfer_to_src_state(src_state, input_content)
                        if not transfer_res:
                            print("### Error: transfer wrong, skip")
                            continue
                    elif src_state == "state_1":
                        print("### Restart app to state_1")
                        self.wait_restart()
                    else:
                        print("### Error: transfer wrong, skip")
                        continue
            view_xpath = view_key.split("###")[1]
            if "KEY#" in view_xpath:
                print("click back")
                self.controller.click_back()
                click_target_res = True
            else:
                if "_FillInfo" in view_xpath:
                    self.controller.detect_edittext_and_fill(input_content)
                    view_xpath = view_xpath.replace("_FillInfo", "")
                print("- click target_view:", target_refer_name, target_bounds)
                click_target_res = self.controller.click_view_by_xpath(view_key)
            if click_target_res:
                dst_state = self.controller.get_current_state()
                if dst_state == "state_0" and not check_crash():
                    relaunch_res = self.controller.relaunch_app()
                    if relaunch_res:
                        dst_state = self.controller.get_current_state()
                if dst_state != "unknown":
                    print("# update view transition:", src_state + "->" + dst_state)
                    self.state_view_info.update_view_transfer(view_key, dst_state)
                else:
                    # current_activity, page_source = self.controller.get_page_info()
                    # new_state_id, new_state_xml_path, new_state_img_path = self.state_view_info.get_new_state_name()
                    # self.controller.save_screen_img(new_state_img_path)
                    # new_state_id = self.state_view_info.add_state(current_activity, page_source, view_key, new_state_id,
                    #                                               new_state_xml_path, new_state_img_path)
                    # print("# find a new state:", new_state_id)
                    self.add_new_state(view_key)
                if dst_state == "crash_page":
                    print("find crash!, stop explore!")
                    crash_click_views = []
                    transfer_views = self.state_view_info.get_transfer_path(cur_state, src_state)
                    for t in transfer_views:
                        crash_click_views.append(t[0])
                    crash_click_views.append(view_key)
                    self.state_view_info.export_crash_steps(crash_click_views)
                    return
            else:
                print("### Error: click view error")
                print(view_xpath)
                print("### try to repair the view")
                temp_long_click = False
                if "_LongClick" in view_xpath:
                    temp_long_click = True
                    view_xpath = view_xpath.replace("_LongClick", "")
                cur_state, edittext_on_page, clickable_view_on_page = self.controller.get_all_xpath_on_page()
                all_views_on_page = edittext_on_page.copy()
                all_views_on_page.update(clickable_view_on_page)
                ori_view_class = target_view.view_class
                ori_view_bounds = target_view.bounds
                find_view_xpath = ""
                for temp_xpath, temp_view in all_views_on_page.items():
                    if temp_view["class"] != ori_view_class:
                        continue
                    temp_view_bounds = temp_view["bounds"]
                    xpath_dis = Levenshtein.distance(view_xpath, temp_xpath)
                    if xpath_dis > 3:
                        continue
                    total_bounds_dis = 0
                    for pos1 in range(2):
                        for pos2 in range(2):
                            total_bounds_dis += abs(temp_view_bounds[pos1][pos2] - ori_view_bounds[pos1][pos2])
                    if total_bounds_dis < 20:
                        find_view_xpath = temp_xpath
                        print("find_view_xpath:", temp_xpath)
                        break
                if len(find_view_xpath) > 0:
                    if temp_long_click:
                        find_view_xpath = find_view_xpath + "_LongClick"
                    print("### find a similar xpath", find_view_xpath)
                    print("               ori xpath", view_xpath)
                    repair_view_key = src_state + "###" + find_view_xpath
                    ori_view = self.state_view_info.views.pop(view_key)
                    self.state_view_info.views.setdefault(repair_view_key, ori_view)
                    click_target_res = self.controller.click_view_by_xpath(repair_view_key)
                    dst_state = self.controller.get_current_state()
                    if dst_state != "unknown":
                        print("# update view transition:", src_state + "->" + dst_state)
                        self.state_view_info.update_view_transfer(repair_view_key, dst_state)
                    else:
                        # current_activity, page_source = self.controller.get_page_info()
                        # new_state_id, new_state_xml_path, new_state_img_path = self.state_view_info.get_new_state_name()
                        # self.controller.save_screen_img(new_state_img_path)
                        # new_state_id = self.state_view_info.add_state(current_activity, page_source, repair_view_key,
                        #                                               new_state_id,
                        #                                               new_state_xml_path, new_state_img_path)
                        # print("# find a new state:", new_state_id)
                        self.add_new_state(repair_view_key)
                else:
                    self.state_view_info.update_view_transfer(view_key, "discard")
            if check_crash():
                print("find crash!, stop explore!")
                crash_click_views = []
                transfer_views = self.state_view_info.get_transfer_path(cur_state, src_state)
                for t in transfer_views:
                    crash_click_views.append(t[0])
                crash_click_views.append(view_key)
                self.state_view_info.export_crash_steps(crash_click_views)
                return
        print("explore finish! restart app")
        self.controller.restart_app()

    def wait_restart(self):
        self.controller.restart_app()
        init_state = self.controller.get_current_state()
        while init_state != "state_1":
            time.sleep(3)
            print("waiting restart! current state:", init_state)
            init_state = self.controller.get_current_state()
        pkg_name = self.controller.get_pkg_name()
        if pkg_name == "org.schabi.newpipe":
            time.sleep(5)

    def transfer_to_src_state_old(self, src_state, input_content, cur_state=""):
        if "state" not in cur_state:
            cur_state = self.controller.get_current_state()
        transfer_views = self.state_view_info.get_transfer_path(cur_state, src_state)
        if len(transfer_views) == 0:
            print("### can't reach, transfer fail")
            return False
        for transfer_idx, (transfer_key, from_state, to_state) in enumerate(transfer_views):
            before_state = self.controller.get_current_state()
            if before_state != from_state:
                print("### Error: unmatch with from_state, expect: " + from_state + ", get: " + before_state)
                return False
            try_time = 0
            after_state = before_state
            transfer_idx_str = "- (" + str(transfer_idx + 1) + "/" + str(len(transfer_views)) + ") "
            while try_time < 3:
                if "KEY#" in transfer_key:
                    print(transfer_idx_str + "transfer by back")
                    self.controller.click_back()
                else:
                    transfer_view = self.state_view_info.views[transfer_key]
                    # cur_dst_not_sure = transfer_view.dst_state_not_sure
                    refer_name = get_view_refer_name(transfer_view)
                    transfer_bounds = transfer_view.bounds
                    print(transfer_idx_str + "transfer by view:", refer_name, transfer_bounds)
                    view_xpath = transfer_key.split("###")[1]
                    if "_FillInfo" in view_xpath:
                        self.controller.detect_edittext_and_fill(input_content)
                        view_xpath = view_xpath.replace("_FillInfo", "")
                    click_res = self.controller.click_view_by_xpath(transfer_key)
                    if not click_res:
                        print("### Error: click view error")
                        print("### try to repair the view")
                        temp_long_click = False
                        if "_LongClick" in view_xpath:
                            temp_long_click = True
                            view_xpath = view_xpath.replace("_LongClick", "")
                        cur_state, edittext_on_page, clickable_view_on_page = self.controller.get_all_xpath_on_page()
                        all_views_on_page = edittext_on_page.copy()
                        all_views_on_page.update(clickable_view_on_page)
                        ori_view_class = transfer_view.view_class
                        ori_view_bounds = transfer_view.bounds
                        find_view_xpath = ""
                        for temp_xpath, temp_view in all_views_on_page.items():
                            if temp_view["class"] != ori_view_class:
                                continue
                            temp_view_bounds = temp_view["bounds"]
                            xpath_dis = Levenshtein.distance(view_xpath, temp_xpath)
                            if xpath_dis > 3:
                                continue
                            total_bounds_dis = 0
                            for pos1 in range(2):
                                for pos2 in range(2):
                                    total_bounds_dis += abs(temp_view_bounds[pos1][pos2] - ori_view_bounds[pos1][pos2])
                            if total_bounds_dis < 10:
                                find_view_xpath = temp_xpath
                                break
                        if len(find_view_xpath) > 0:
                            if temp_long_click:
                                find_view_xpath = find_view_xpath + "_LongClick"
                                view_xpath = view_xpath + "_LongClick"
                            print("### find a similar xpath", find_view_xpath)
                            print("               ori xpath", view_xpath)
                        self.state_view_info.update_view_transfer(transfer_key, "discard")
                        if len(find_view_xpath) > 0:
                            if temp_long_click:
                                find_view_xpath = find_view_xpath + "_LongClick"
                            print("### find a similar xpath", find_view_xpath)
                            print("               ori xpath", view_xpath)
                            repair_view_key = transfer_key.split("###")[0] + "###" + find_view_xpath
                            ori_view = self.state_view_info.views.pop(transfer_key)
                            self.state_view_info.views.setdefault(repair_view_key, ori_view)
                            click_res = self.controller.click_view_by_xpath(repair_view_key)
                        else:
                            self.state_view_info.update_view_transfer(transfer_key, "discard")
                            return False
                time.sleep(1)
                after_state = self.controller.get_current_state()
                if after_state == before_state and after_state != to_state:
                    print("# state not change, try again")
                    try_time += 1
                else:
                    break
            if after_state == "state_0" and not check_crash():
                relaunch_res = self.controller.relaunch_app()
                if relaunch_res:
                    after_state = self.controller.get_current_state()
            if after_state != to_state:
                print("### Error: unmatch with to_state, expect: " + to_state + ", get: " + after_state)
                cur_activity, page_source = self.controller.get_page_info()
                # with open("../Temp/" + to_state + "_" + str(time.time()) + ".txt", "w", encoding="UTF-8") as f:
                #     f.write(page_source)
                #     f.close()
                if "state_" in after_state and after_state != "state_0":
                    # print(self.state_view_info.view_xpath_transition[from_state][to_state])
                    # print(transfer_key)
                    self.state_view_info.update_view_transfer(transfer_key, after_state)
                    # print(self.state_view_info.views[transfer_key].dst_state)
                    # print(self.state_view_info.view_xpath_transition[from_state][to_state])
                elif after_state == "unknown":
                    # current_activity, page_source = self.controller.get_page_info()
                    # new_state_id, new_state_xml_path, new_state_img_path = self.state_view_info.get_new_state_name()
                    # self.controller.save_screen_img(new_state_img_path)
                    # new_state_id = self.state_view_info.add_state(current_activity, page_source, transfer_key,
                    #                                               new_state_id,
                    #                                               new_state_xml_path, new_state_img_path)
                    # print("# find a new state:", new_state_id)
                    self.add_new_state(transfer_key)
                return False
        finish_state = self.controller.get_current_state()
        if finish_state != src_state:
            print("### transfer fail")
            return False
        print("- transfer done!")
        return True

    def transfer_to_src_state(self, src_state, input_content):
        while True:
            cur_state = self.controller.get_current_state()
            transfer_views = self.state_view_info.get_transfer_path(cur_state, src_state)
            if len(transfer_views) == 0:
                print("### can't reach, transfer fail")
                return False
            for transfer_idx, (transfer_key, from_state, to_state) in enumerate(transfer_views):
                before_state = self.controller.get_current_state()
                if before_state != from_state:
                    print("### Error: unmatch with from_state, expect: " + from_state + ", get: " + before_state,
                          ", get transfer path again")
                    continue
                try_time = 0
                after_state = before_state
                transfer_idx_str = "- (" + str(transfer_idx + 1) + "/" + str(len(transfer_views)) + ") "
                transfer_view = self.state_view_info.views[transfer_key]
                refer_name = get_view_refer_name(transfer_view)
                transfer_bounds = transfer_view.bounds
                while try_time < 3:
                    if "KEY#" in transfer_key:
                        print(transfer_idx_str + "transfer by back")
                        self.controller.click_back()
                    else:
                        print(transfer_idx_str + "transfer by view:", refer_name, transfer_bounds)
                        view_xpath = transfer_key.split("###")[1]
                        if "_FillInfo" in view_xpath:
                            self.controller.detect_edittext_and_fill(input_content)
                            view_xpath = view_xpath.replace("_FillInfo", "")
                        click_res = self.controller.click_view_by_xpath(transfer_key)
                        if not click_res:
                            print("### Error: click view error")
                            print("### try to repair the view")
                            temp_long_click = False
                            if "_LongClick" in view_xpath:
                                temp_long_click = True
                                view_xpath = view_xpath.replace("_LongClick", "")
                            cur_state, edittext_on_page, clickable_view_on_page = self.controller.get_all_xpath_on_page()
                            all_views_on_page = edittext_on_page.copy()
                            all_views_on_page.update(clickable_view_on_page)
                            ori_view_class = transfer_view.view_class
                            ori_view_bounds = transfer_view.bounds
                            find_view_xpath = ""
                            for temp_xpath, temp_view in all_views_on_page.items():
                                if temp_view["class"] != ori_view_class:
                                    continue
                                temp_view_bounds = temp_view["bounds"]
                                xpath_dis = Levenshtein.distance(view_xpath, temp_xpath)
                                if xpath_dis > 3:
                                    continue
                                total_bounds_dis = 0
                                for pos1 in range(2):
                                    for pos2 in range(2):
                                        total_bounds_dis += abs(
                                            temp_view_bounds[pos1][pos2] - ori_view_bounds[pos1][pos2])
                                if total_bounds_dis < 10:
                                    find_view_xpath = temp_xpath
                                    break
                            if len(find_view_xpath) > 0:
                                if temp_long_click:
                                    find_view_xpath = find_view_xpath + "_LongClick"
                                    view_xpath = view_xpath + "_LongClick"
                                print("### find a similar xpath", find_view_xpath)
                                print("               ori xpath", view_xpath)
                            self.state_view_info.update_view_transfer(transfer_key, "discard")
                            if len(find_view_xpath) > 0:
                                if temp_long_click:
                                    find_view_xpath = find_view_xpath + "_LongClick"
                                print("### find a similar xpath", find_view_xpath)
                                print("               ori xpath", view_xpath)
                                repair_view_key = transfer_key.split("###")[0] + "###" + find_view_xpath
                                ori_view = self.state_view_info.views.pop(transfer_key)
                                self.state_view_info.views.setdefault(repair_view_key, ori_view)
                                click_res = self.controller.click_view_by_xpath(repair_view_key)
                            else:
                                self.state_view_info.update_view_transfer(transfer_key, "discard")
                                return False
                    time.sleep(1)
                    after_state = self.controller.get_current_state()
                    if after_state == before_state and after_state != to_state:
                        print("# state not change, try again")
                        try_time += 1
                    else:
                        break
                if after_state == "state_0" and not check_crash():
                    relaunch_res = self.controller.relaunch_app()
                    if relaunch_res:
                        after_state = self.controller.get_current_state()
                if after_state != to_state:
                    print("### Error: unmatch with to_state, expect: " + to_state + ", get: " + after_state)
                    cur_activity, page_source = self.controller.get_page_info()
                    # with open("../Temp/" + to_state + "_" + str(time.time()) + ".txt", "w", encoding="UTF-8") as f:
                    #     f.write(page_source)
                    #     f.close()
                    if "state_" in after_state and after_state != "state_0":
                        if refer_name != "back" or transfer_view.dst_state_not_sure:
                            # print(self.state_view_info.view_xpath_transition[from_state][to_state])
                            # print(transfer_key)
                            self.state_view_info.update_view_transfer(transfer_key, after_state)
                            # print(self.state_view_info.views[transfer_key].dst_state)
                            # print(self.state_view_info.view_xpath_transition[from_state][to_state])
                    elif after_state == "unknown":
                        # current_activity, page_source = self.controller.get_page_info()
                        # new_state_id, new_state_xml_path, new_state_img_path = self.state_view_info.get_new_state_name()
                        # self.controller.save_screen_img(new_state_img_path)
                        # new_state_id = self.state_view_info.add_state(current_activity, page_source, transfer_key,
                        #                                               new_state_id,
                        #                                               new_state_xml_path, new_state_img_path)
                        # print("# find a new state:", new_state_id)
                        self.add_new_state(transfer_key)
                    if after_state == src_state:
                        return True
                    else:
                        return False
            finish_state = self.controller.get_current_state()
            if finish_state != src_state:
                print("### transfer fail")
                return False
            print("- transfer done!")
            return True

    def get_not_sure_need_to_clean(self, relevant_states: set):
        need_to_clean_states = set()
        sure_states = set()
        for tdst_state in relevant_states:
            need_to_clean = True
            cur_pre_states = set()
            for view_key, view in self.state_view_info.views.items():
                if view.dst_state == tdst_state:
                    if view.dst_state_not_sure:
                        cur_pre_states.add(view.src_state)
                    else:
                        need_to_clean = False
                        break
            if need_to_clean:
                need_to_clean_states = need_to_clean_states.union(cur_pre_states)
            else:
                sure_states.add(tdst_state)
        return need_to_clean_states, sure_states

    def add_new_state(self, view_key):
        current_activity, page_source = self.controller.get_page_info()
        new_state_id, new_state_xml_path, new_state_img_path = self.state_view_info.get_new_state_name()
        self.controller.save_screen_img(new_state_img_path)
        has_find_views = set()
        new_state_id = self.state_view_info.add_state(current_activity, page_source, view_key, new_state_id,
                                                      new_state_xml_path, new_state_img_path, has_find_views)
        need_scroll = has_scroll_view(page_source)
        if need_scroll:
            scroll_times = 0
            while scroll_times < 3:
                scroll_times += 1
                try:
                    self.controller.swipe_down()
                    time.sleep(2.5)
                    current_activity, page_source = self.controller.get_page_info()
                    self.state_view_info.add_scroll_state(page_source, new_state_id, new_state_img_path, has_find_views)
                except Exception as e:
                    break
        print("# find a new state:", new_state_id)
        print("# try back for new state")
        self.controller.click_back()
        time.sleep(1.5)
        back_state = self.controller.get_current_state()
        if "state" in back_state:
            print("# back state=", back_state)
            back_view_key = new_state_id + "###" + "KEY#BACK"
            self.state_view_info.views[back_view_key].dst_state = back_state
            self.state_view_info.views[back_view_key].dst_state_not_sure = False
        else:
            back_view_key = new_state_id + "###" + "KEY#BACK"
            self.add_new_state(back_view_key)
