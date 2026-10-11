    if (kk_shen_machine__is_Recover(_uniq_x_10236, _ctx)) {
      struct kk_shen_machine_Recover* _con_x2310 = kk_shen_machine__as_Recover(_uniq_x_10236, _ctx);
      kk_string_t _pat_14 = _con_x2310->message;
      kk_reuse_drop(_ru_x1579,kk_context());
      if kk_likely(kk_datatype_ptr_is_unique(_uniq_x_10236, _ctx)) {
        kk_string_drop(_pat_14, _ctx);
        kk_datatype_ptr_free(_uniq_x_10236, _ctx);
      }
      else {
        kk_datatype_ptr_decref(_uniq_x_10236, _ctx);
      }
    }
    {
      struct kk_shen_machine_ApplyRest* _con_x2311 = kk_shen_machine__as_ApplyRest(_uniq_x_10236, _ctx);
      kk_std_core_types__list args_1 = _con_x2311->args;
      kk_reuse_drop(_ru_x1579,kk_context());
      if kk_likely(kk_datatype_ptr_is_unique(_uniq_x_10236, _ctx)) {
        kk_datatype_ptr_free(_uniq_x_10236, _ctx);
      }
      else {
        kk_std_core_types__list_dup(args_1, _ctx);
        kk_datatype_ptr_decref(_uniq_x_10236, _ctx);
      }
      kk_std_core_types__list ys_4_10058;
      kk_box_t _x_x2312;
      kk_ref_t _x_x2313 = kk_ref_dup(vs, _ctx); /*local-var<3812,list<shen/values/value>>*/
      _x_x2312 = kk_ref_get(_x_x2313,kk_context()); /*298*/
      ys_4_10058 = kk_std_core_types__list_unbox(_x_x2312, KK_OWNED, _ctx); /*list<shen/values/value>*/
      kk_std_core_types__list _b_x654_662;
      if (kk_std_core_types__is_Nil(args_1, _ctx)) {
        _b_x654_662 = ys_4_10058; /*list<shen/values/value>*/
      }
      else {
        _b_x654_662 = kk_std_core_list__unroll_append_10004(args_1, ys_4_10058, _ctx); /*list<shen/values/value>*/
      }
      kk_ref_set_borrow(vs,(kk_std_core_types__list_box(_b_x654_662, _ctx)),kk_context());
