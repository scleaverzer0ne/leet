from pandas import read_excel


def parse_tt(uid, file_path):
    time_table = {}
    # ToDo: Fetch existing faculties from the department and store their facultyIDs in list to cross check them with the parsed excel
    # faculties = get_faculties(fac_head=uid)

    tt = read_excel(file_path)

    for row in range(len(tt)):
        day = dict(tt.loc[row])
        # print(day)
        # print(type(day))
        tt_day = {}
        lec_num = 1
        for k, v in day.items():
            if k == 'Day':
                continue
            lec_start_time, lec_end_time = k.split('-')
            lec_name, lec_faculty = v.split(',')
            lec = {
                'lec_name': lec_name.strip(),
                'lec_faculty': lec_faculty.strip(),
                'lec_start_time': lec_start_time.strip(),
                'lec_end_time': lec_end_time.strip(),
            }
            tt_day[str(lec_num)] = lec
            # print(k, v)
            # print(day['Day'])
            lec_num += 1
        time_table[day['Day']] = tt_day

    return time_table