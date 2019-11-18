from haven.data.tiers import Tier


def insert(model_cls,
           **kwargs):
    q = model_cls(**kwargs)
    q.full_clean()
    q.save()
    return q


def insert_initial_policies(policy_group_model_cls,
                            policy_model_cls,
                            policy_assignment_model_cls):
    # This method should only be called on an empty database (i.e. on first
    # migration or during tests). If you make changes, they will not be
    # reflected in the actual database unless you make a related migration.
    connection_group = insert(
        policy_group_model_cls,
        name='connection',
        description='Connection')
    copy_group = insert(
        policy_group_model_cls,
        name='copy',
        description='Copy-paste')
    egress_group = insert(
        policy_group_model_cls,
        name='egress',
        description='Data egress')
    ingress_group = insert(
        policy_group_model_cls,
        name='ingress',
        description='Data ingress')
    inbound_group = insert(
        policy_group_model_cls,
        name='inbound',
        description='Inbound network')
    internet_group = insert(
        policy_group_model_cls,
        name='internet',
        description='Internet access')
    outbound_group = insert(
        policy_group_model_cls,
        name='outbound',
        description='Outbound network')
    mirror_group = insert(
        policy_group_model_cls,
        name='mirror',
        description='Package mirrors')
    physical_group = insert(
        policy_group_model_cls,
        name='physical',
        description='Physical security')
    ref_class_group = insert(
        policy_group_model_cls,
        name='ref_class',
        description='Refereeing of classification')
    ref_reclass_group = insert(
        policy_group_model_cls,
        name='ref_reclass',
        description='Refereeing of reclassification')
    software_group = insert(
        policy_group_model_cls,
        name='software',
        description='Software ingress')
    tier_group = insert(
        policy_group_model_cls,
        name='tier',
        description='Tier')
    device_group = insert(
        policy_group_model_cls,
        name='device',
        description='User devices')
    user_group = insert(
        policy_group_model_cls,
        name='user',
        description='User management')

    connection_rdp_policy = insert(
        policy_model_cls,
        group=connection_group,
        name='connection_rdp',
        description='Only remote desktop access is enabled.')
    connection_ssh_policy = insert(
        policy_model_cls,
        group=connection_group,
        name='connection_ssh',
        description='SSH access to the environment is possible without '
                    'restrictions. The user should be able to set up port '
                    'forwarding (ssh tunnel) and use this to access '
                    'remotely-running UI clients via a native client browser.')
    copy_allowed_policy = insert(
        policy_model_cls,
        group=copy_group,
        name='copy_allowed',
        description='Copy-out should be permitted where a user believes their '
                    'local device is secure, with the permission of the Investigator.')
    copy_forbidden_policy = insert(
        policy_model_cls,
        group=copy_group,
        name='copy_forbidden',
        description='Copy-paste is disabled on the remote desktop.')
    copy_restricted_policy = insert(
        policy_model_cls,
        group=copy_group,
        name='copy_restricted',
        description='Copy-paste out of the secure research environment must '
                    'be forbidden by policy, but not enforced by '
                    'configuration, unlike in Tier 3. Users must have to '
                    'confirm they understand and accept the policy on signup '
                    'using the web management framework.')
    device_managed_policy = insert(
        policy_model_cls,
        group=device_group,
        name='device_managed',
        description='Managed laptop devices should be able to leave the '
                    'physical office where the Restricted network exists, but '
                    'should have no access to environments while ’roaming’.')
    device_open_policy = insert(
        policy_model_cls,
        group=device_group,
        name='device_open',
        description='Open devices should allowed.')
    egress_signoff_policy = insert(
        policy_model_cls,
        group=egress_group,
        name='egress_signoff',
        description='Data Provider Representative signoff of all egress of '
                    'data or code from the environment is required.')
    egress_allowed_policy = insert(
        policy_model_cls,
        group=egress_group,
        name='egress_allowed',
        description='Data Provider Representative signoff of egress of data '
                    'or code is not required.')
    inbound_instiution_policy = insert(
        policy_model_cls,
        group=inbound_group,
        name='inbound_institution',
        description='Access nodes should only be accessible from an '
                    'Institutional network.')
    inbound_open_policy = insert(
        policy_model_cls,
        group=inbound_group,
        name='inbound_open',
        description='Environments should be accessible from the Internet.')
    inbound_restricted_policy = insert(
        policy_model_cls,
        group=inbound_group,
        name='inbound_restricted',
        description='Only the Restricted network will be able to access nodes.')
    ingress_secure_policy = insert(
        policy_model_cls,
        group=ingress_group,
        name='ingress_secure',
        description='High-security data transfer process is required.')
    ingress_open_policy = insert(
        policy_model_cls,
        group=ingress_group,
        name='ingress_open',
        description='Lower-security data transfer processes are allowed.')
    internet_allowed_policy = insert(
        policy_model_cls,
        group=internet_group,
        name='internet_allowed',
        description='Environments have access to the internet.')
    internet_forbidden_policy = insert(
        policy_model_cls,
        group=internet_group,
        name='internet_forbidden',
        description='Environments have no access to the internet, other than '
                    'inbound through the access connection.')
    mirror_open_policy = insert(
        policy_model_cls,
        group=mirror_group,
        name='mirror_open',
        description='Installation should be from the reference package server '
                    'on the external internet.')
    mirror_delay_policy = insert(
        policy_model_cls,
        group=mirror_group,
        name='mirror_delay',
        description='Package mirrors should include all software, one month '
                    'behind the reference package server. Critical security '
                    'updates should be fast-tracked.')
    mirror_whitelist_policy = insert(
        policy_model_cls,
        group=mirror_group,
        name='mirror_whitelist',
        description='Package mirrors should include only white-listed '
                    'software.')
    outbound_open_policy = insert(
        policy_model_cls,
        group=outbound_group,
        name='outbound_open',
        description='The internet is accessible from inside the environment.')
    outbound_restricted_policy = insert(
        policy_model_cls,
        group=outbound_group,
        name='outbound_restricted',
        description='The virtual network inside the environment is '
                    'completely isolated.')
    physical_high_policy = insert(
        policy_model_cls,
        group=physical_group,
        name='physical_high',
        description='Access must be from the high security space.')
    physical_medium_policy = insert(
        policy_model_cls,
        group=physical_group,
        name='physical_medium',
        description='Access should be from the medium security space.')
    physical_open_policy = insert(
        policy_model_cls,
        group=physical_group,
        name='physical_open',
        description='Not subject to physical security.')
    ref_class_open_policy = insert(
        policy_model_cls,
        group=ref_class_group,
        name='ref_class_open',
        description='Independent Referee scrutiny of data classification is '
                    'not required.')
    ref_class_required_policy = insert(
        policy_model_cls,
        group=ref_class_group,
        name='ref_class_required',
        description='Independent Referee scrutiny of data classification is '
                    'required.')
    ref_reclass_open_policy = insert(
        policy_model_cls,
        group=ref_reclass_group,
        name='ref_reclass_open',
        description='Independent Referee scrutiny of data reclassification '
                    'to a lower tier is not required.')
    ref_reclass_required_policy = insert(
        policy_model_cls,
        group=ref_reclass_group,
        name='ref_reclass_required',
        description='Independent Referee scrutiny of data reclassification '
                    'to a lower tier is required.')
    software_airlock_policy = insert(
        policy_model_cls,
        group=software_group,
        name='software_airlock',
        description='Additional software or virtual machines arriving through '
                    'the software ingress process must be installed in an '
                    'environment with no access to the data (with the '
                    'exception of pre-approved virtual machines or package '
                    'mirrors).')
    software_signoff_policy = insert(
        policy_model_cls,
        group=software_group,
        name='software_signoff',
        description='Additional software or virtual machines arriving through '
                    'the software ingress process must be reviewed and signed '
                    'off by the Investigator and Referee before it can be '
                    'accessed inside the environment (with the exception of '
                    'pre-approved virtual machines or package mirrors).')
    software_open_policy = insert(
        policy_model_cls,
        group=software_group,
        name='software_open',
        description='Users should be able to install software directly into '
                    'the environment (in user space) from the open internet.')
    tier_0_policy = insert(
        policy_model_cls,
        group=tier_group,
        name='tier_0',
        description='0')
    tier_1_policy = insert(
        policy_model_cls,
        group=tier_group,
        name='tier_1',
        description='1')
    tier_2_policy = insert(
        policy_model_cls,
        group=tier_group,
        name='tier_2',
        description='2')
    tier_3_policy = insert(
        policy_model_cls,
        group=tier_group,
        name='tier_3',
        description='3')
    tier_4_policy = insert(
        policy_model_cls,
        group=tier_group,
        name='tier_4',
        description='4')
    user_signoff_policy = insert(
        policy_model_cls,
        group=user_group,
        name='user_signoff',
        description='New Referees or members of the research team must be '
                    'counter-approved by the Dataset Provider Representative.')
    user_open_policy = insert(
        policy_model_cls,
        group=user_group,
        name='user_open',
        description='The Investigator has the authority to add new members '
                    'to the research team, and the Research Manager has the '
                    'authority to assign Referees.')

    insert(
        policy_assignment_model_cls,
        tier=Tier.ZERO,
        policy=tier_0_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ZERO,
        policy=mirror_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ZERO,
        policy=inbound_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ZERO,
        policy=outbound_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ZERO,
        policy=device_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ZERO,
        policy=physical_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ZERO,
        policy=user_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ZERO,
        policy=connection_ssh_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ZERO,
        policy=internet_allowed_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ZERO,
        policy=software_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ZERO,
        policy=ingress_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ZERO,
        policy=copy_allowed_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ZERO,
        policy=ref_class_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ZERO,
        policy=ref_reclass_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ZERO,
        policy=egress_allowed_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ONE,
        policy=tier_1_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ONE,
        policy=mirror_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ONE,
        policy=inbound_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ONE,
        policy=outbound_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ONE,
        policy=device_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ONE,
        policy=physical_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ONE,
        policy=user_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ONE,
        policy=connection_ssh_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ONE,
        policy=internet_allowed_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ONE,
        policy=software_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ONE,
        policy=ingress_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ONE,
        policy=copy_allowed_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ONE,
        policy=ref_class_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ONE,
        policy=ref_reclass_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.ONE,
        policy=egress_allowed_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.TWO,
        policy=tier_2_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.TWO,
        policy=mirror_delay_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.TWO,
        policy=inbound_instiution_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.TWO,
        policy=outbound_restricted_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.TWO,
        policy=device_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.TWO,
        policy=physical_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.TWO,
        policy=user_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.TWO,
        policy=connection_rdp_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.TWO,
        policy=internet_forbidden_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.TWO,
        policy=software_airlock_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.TWO,
        policy=ingress_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.TWO,
        policy=copy_restricted_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.TWO,
        policy=ref_class_required_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.TWO,
        policy=ref_reclass_open_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.TWO,
        policy=egress_allowed_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.THREE,
        policy=tier_3_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.THREE,
        policy=mirror_whitelist_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.THREE,
        policy=inbound_restricted_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.THREE,
        policy=outbound_restricted_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.THREE,
        policy=device_managed_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.THREE,
        policy=physical_medium_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.THREE,
        policy=user_signoff_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.THREE,
        policy=connection_rdp_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.THREE,
        policy=internet_forbidden_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.THREE,
        policy=software_signoff_policy)
    insert(
        policy_assignment_model_cls,

        tier=Tier.THREE,
        policy=ingress_secure_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.THREE,
        policy=copy_forbidden_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.THREE,
        policy=ref_class_required_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.THREE,
        policy=ref_reclass_required_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.THREE,
        policy=egress_signoff_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.FOUR,
        policy=tier_4_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.FOUR,
        policy=mirror_whitelist_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.FOUR,
        policy=inbound_restricted_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.FOUR,
        policy=outbound_restricted_policy)
    insert(
        policy_assignment_model_cls,

        tier=Tier.FOUR,
        policy=device_managed_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.FOUR,
        policy=physical_high_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.FOUR,
        policy=user_signoff_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.FOUR,
        policy=connection_rdp_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.FOUR,
        policy=internet_forbidden_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.FOUR,
        policy=software_signoff_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.FOUR,
        policy=ingress_secure_policy)
    insert(
        policy_assignment_model_cls,

        tier=Tier.FOUR,
        policy=copy_forbidden_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.FOUR,

        policy=ref_class_required_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.FOUR,
        policy=ref_reclass_required_policy)
    insert(
        policy_assignment_model_cls,
        tier=Tier.FOUR,
        policy=egress_signoff_policy)
