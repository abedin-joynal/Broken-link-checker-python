<?php
/*
Plugin Name: 0Broken Link Checker
Plugin URI: http://localhost
Description: This is a plugin to check broken links on the site. 
Author: Juhwan Yoo
Version: 1.0
Author URI: http://localhost
*/
global $jal_db_version;
$jal_db_version = '1.0';
$msg_body="";
register_activation_hook (__FILE__, 'jal_brokenlink_install');
function jal_brokenlink_install() {
	global $wpdb;
	$table_name = $wpdb->prefix . 'brokenlink';
	$charset_collate = $wpdb->get_charset_collate();
	$sql = "CREATE TABLE $table_name (
		id mediumint(9) NOT NULL AUTO_INCREMENT,
		time datetime DEFAULT '0000-00-00 00:00:00' NOT NULL,
		knox_id tinytext NOT NULL,
		email tinytext NOT NULL,
		full_name tinytext NOT NULL,
		employee_number tinytext NOT NULL,
		user_information tinytext NOT NULL,
		department_name tinytext NOT NULL,
		target_url varchar(155) DEFAULT '' NOT NULL,
		total_number mediumint(9) NOT NULL,
		broken_number mediumint(9) NOT NULL,
		result_url varchar(155) DEFAULT '' NOT NULL,
		PRIMARY KEY  (id)
	) $charset_collate;";
	require_once( ABSPATH . 'wp-admin/includes/upgrade.php' );
	dbDelta( $sql );
	add_option( 'jal_db_version', $jal_db_version );
	update_option( 'plugin_type', 'brokenlinkchecker');
	$installed_ver = get_option( "jal_db_version" );
	if ( $installed_ver != $jal_db_version ) {
		$table_name = $wpdb->prefix . 'liveshoutbox';
		$sql = "CREATE TABLE $table_name (
			id mediumint(9) NOT NULL AUTO_INCREMENT,
			time datetime DEFAULT '0000-00-00 00:00:00' NOT NULL,
			knox_id tinytext NOT NULL,
			email tinytext NOT NULL,
			full_name tinytext NOT NULL,
			employee_number tinytext NOT NULL,
			user_information tinytext NOT NULL,
			department_name tinytext NOT NULL,
			target_url varchar(155) DEFAULT '' NOT NULL,
			total_number mediumint(9) NOT NULL,
			broken_number mediumint(9) NOT NULL,
			result_url varchar(155) DEFAULT '' NOT NULL,
			PRIMARY KEY  (id)
		);";
		require_once( ABSPATH . 'wp-admin/includes/upgrade.php' );
		dbDelta( $sql );
		update_option( "jal_db_version", $jal_db_version );
	}
}
register_deactivation_hook(__FILE__, 'jal_brokenlink_deactivate');
function jal_brokenlink_deactivate(){
	if(wp_style_is('brokenlink_style', $list='registered')){
		wp_deregister_style('brokenlink_style');
	}
	if(wp_script_is('brokenlink_script', $list='registered')){
		wp_deregister_script('brokenlink_script');
	}
	if(wp_style_is('brokenlink_style', $list='enqueued')){
		wp_dequeue_style('brokenlink_style');
	}
	if(wp_script_is('brokenlink_script', $list='enqueued')){
		wp_dequeue_script('brokenlink_script');
	}
	wp_clear_scheduled_hook('save_sessions_hook');
}

add_action('wp_enqueue_scripts', 'fwds_brokenlink_styles', 20);
function fwds_brokenlink_styles() {
	global $post;
	if (has_shortcode($post->post_content, "my_brokenlink")):
		wp_enqueue_style('brokenlink_style', plugins_url('css/style.css', __FILE__));
		wp_enqueue_script('brokenlink_script', plugins_url( 'js/main.js', __FILE__ ) );
		wp_localize_script( 'brokenlink_script', 'ajax_object', array( 'ajax_url' => admin_url( 'admin-ajax.php')));
	endif;
}

add_shortcode('my_brokenlink', 'wp_brokenlink_checker');
function wp_brokenlink_checker() {

	if ( is_user_logged_in() ) {
		$current_time = current_time('mysql');
		$current_user = wp_get_current_user();
		$str = $current_user->mo_ldap_local_custom_attribute_distinguishedname;
		$strTok = explode(',', $str);
		$count = count($strTok);
		$searchName = 'OU=';
		$distinguish_name = '';
		for($i = 0;$i < $count;$i++){
			if (strpos($strTok[$i], $searchName) !== false){ 
				array_push($strTok, str_replace($searchName, '', $strTok[$i]));
			}
			unset($strTok[$i]);
		}
		$strTok = array_reverse(array_values($strTok));
		for($i = 3;$i < count($strTok);$i++){
			if ($i !== 3) $distinguish_name .= ' > ';
			$distinguish_name .= $strTok[$i];
		}
		$html = '
<form action="#v_form" method="post" id="v_form" onsubmit="return validate(this);">
<h3>Required data</h3>
<table class="custom-table">
	<tr>
		<td class="header" ><label for="target_url">target URL</label></td>
		<td class="input-cell"><input type="text" name="target_url" id="target_url" onfocusout="testUrl()" placeholder="Please input the target URL you want to check broken links." /></td></tr>
	</table>
<button type="button" class="collapsible"> Optional data
</button>
<div class="hidden_content">
<table class="custom-table">
	<tr id="row_branch">
	<td class="header" ><label for="git_branch">Git Branch</label></td>
	<td class="input-cell"><input type="text" name="git_branch" id="git_branch" placeholder="Default value: master" /></td></tr>
	<tr>
		<td class="header" ><label for="max_depth">Max Depth</label></td>
		<td class="input-cell"><input type="text" name="max_depth" id="max_depth" placeholder="Default value: unlimited" /></td></tr>
	<tr>
		<td class="header" ><label for="max_thread">Max Thread</label></td>
		<td class="input-cell"><input type="text" name="max_thread" id="max_thread" placeholder="Default value: 15" /></td></tr>
</table>
</div>
<h3>Client information</h3>
<table>
	<tr>
		<td class="header" ><label for="time">time</label></td>
		<td><input type="text" name="time" id="time" value="'.$current_time.'" /></td></tr>
	<tr>
		<td class="header" ><label for="knox_id">Knox ID</label></td>
		<td><input type="text" name="knox_id" id="knox_id" value="'.$current_user->user_login.'" /></td></tr>
	<tr>
		<td class="header" ><label for="email">email</label></td>
		<td><input type="email" name="email" id="email" value="'.$current_user->user_email.'" /></td></tr>
	<tr>
		<td class="header" ><label for="full_name">full name</label></td>
		<td><input type="text" name="full_name" id="full_name" value="'.$current_user->display_name.'" /></td></tr>
	<tr>
		<td class="header" ><label for="employee_number">employee number</label></td>
		<td><input type="text" name="employee_number" id="employee_number" value="'.$current_user->mo_ldap_local_custom_attribute_employeenumber.'" /></td></tr>
	<tr>
		<td class="header" ><label for="department_name">department name</label></td>
		<td><input type="text" name="department_name" id="department_name" value="'.$distinguish_name.'" /></td></tr>
	<tr>
		<td class="header" ><label for="user_information">user information</label></td>
		<td><input type="text" width="100%" name="user_information" id="user_information" value="'.$current_user->mo_ldap_local_custom_attribute_displayname.'" /></td></tr>
</table>
<div class="loading2">
<label id="message"></label>
<img id="loading" src="/images/Preloader_7.gif" alt="" />

</div>
<input type="submit" id="submit" name="submit_form" value="submit" /><br>
</form>
';
		ob_start();
		echo $html;
		#var_dump(wp_get_theme());
		$html = ob_get_clean();
		// does the inserting, in case the form is filled and submitted
		if ( isset( $_POST["submit_form"] ) && $_POST["target_url"] != "" ) {
			$table_name = $wpdb->prefix . 'brokenlink';
			// $time = strip_tags($_POST["time"], "");
			$time = date('Y-m-d H:i:s', time());
			$knox_id = strip_tags($_POST["knox_id"], "");
			$email = strip_tags($_POST["email"], "");
			$full_name = strip_tags($_POST["full_name"], "");
			$employee_number = strip_tags($_POST["employee_number"], "");
			$department_name = strip_tags($_POST["department_name"], "");
			$user_information = strip_tags($_POST["user_information"], "");
			$target_url = strip_tags($_POST["target_url"], "");
			$max_depth = strip_tags($_POST["max_depth"], "");
			$max_thread = strip_tags($_POST["max_thread"], "");
			$git_branch = strip_tags($_POST["git_branch"], "");
			
    			$html = '
<br>
<br><h3>Submitted data</h3>
<table>
	<tr>
		<td class="header">target URL</td>
		<td>'.$target_url.'</td></tr>
	<tr>
		<td class="header">Git Branch</td>
		<td>'.$git_branch.'</td></tr>
	<tr>
		<td class="header">Max Depth</td>
		<td>'.$max_depth.'</td></tr>
	<tr>
		<td class="header">Max Thread</td>
		<td>'.$max_thread.'</td></tr>
	<tr>
		<td class="header">time</td>
		<td>'.$time.'</td></tr>
	<tr>
		<td class="header">Knox ID</td>
		<td>'.$knox_id.'</td></tr>
	<tr>
		<td class="header">email</td>
		<td>'.$email.'</td></tr>
	<tr>
		<td class="header">full name</td>
		<td>'.$full_name.'</td></tr>
	<tr>
		<td class="header">employee number</td>
		<td>'.$employee_number.'</td></tr>
	<tr>
		<td class="header">department name</td>
		<td>'.$department_name.'</td></tr>
	<tr>
		<td class="header">user information</td>
		<td>'.$user_information.'</td></tr>
</table>
';
			$total_count = 0;
			$broken_count = 0;
			$pluginpath = plugin_dir_path(__FILE__);
			$filename = str_replace(' ', '_', str_replace(':', '-', $time)).'_'.str_replace('/', '_', str_replace('://', '_', $target_url));
			$filepath = home_url()."/result/".$filename;
			$logpath = $filepath.".log";
			$filepath = $filepath.".csv";
			$html .= '<h6>Your request was successfully submitted and completed. Thanks!!</h6>';
			// $html .= '<meta http-equiv="refresh" content="3; url='.get_permalink().'">';
			#$target_url = str_replace(' ', '_', $target_url);
			$command = $pluginpath.'python-scripts/start.sh "'.$pluginpath.'python-scripts/linkcollector.py" "'.$target_url.'" "'.$filename.'.csv" "'.$filename.'.log"'.' '.$max_thread.' '.$max_depth.' '.$git_branch;
			#echo $command;
			$descriptorspec = array(
				0 => array("pipe", "r"),
				1 => array("pipe", "w"),
				2 => array("file", "./result/error-output-broken.log", "w"),
			);

			$env = array(
				'LANG' => 'en_US.utf-8',
				'db_user' => DB_USER,
				'db_password' => DB_PASSWORD,
				'secret_key' => DB_SECRET_KEY,
				'db_name' => DB_NAME
			);

			$process = proc_open($command, $descriptorspec, $pipes, NULL, $env);
			echo '<h3>Result</h3>';
			if (is_resource($process)) {
				fwrite($pipes[0]);
				$current = "";
				while(!feof($pipes[1])) {
					$message = fgets($pipes[1], 1024);
					$current .= $message. "\r\n";
					if (strpos($message, 'number of links excluding duplication') !== False) {
						print_wp($message);
						$contents = explode('is', $message);
						$total_count = (int)(end($contents));
					}else if(strpos($message, 'number of broken link') !== False){
						print_wp($message);
						$contents = explode('is', $message);
						$broken_count = (int)(end($contents));
					}else if(strpos($message, "[ERROR] ")!== FALSE){
						print_wp($message);
					}
				}
				fclose($pipes[1]);
				#echo nl2br($logpath);
				#echo nl2br(getcwd());
				file_put_contents (getcwd()."/result/".$filename.".log" , $current);
				$return_value = proc_close($process);
				$message = "[END] Command returned $return_value";
				//$message .= "<br>+ Please check "."<a href=\"".$filepath."\" target=\"_blank_\">the result file</a>"." for details.";
				$message .= "<br>+ Please check the "."<a href=\"".$filepath."\" target=\"_blank_\">result file</a>"." and "."<a href=\"".$logpath."\" target=\"_blank_\">log file</a>"." for details.";
				if ($broken_count == 0) {
					$message .= "<br>+ There is no Broken link ";
				}
				else {
					$message .= "<br>+ There are $broken_count Broken Links ";
				}
				$message .= "@ <a href=\"".$target_url."\" target=\"_blank_\">".$target_url."</a>";
				#$message .= "@ ".$target_url;
				print_wp($message);
			}
			else {
				$filepath = "";
			}
			global $wpdb;
			$table_name = $wpdb->prefix . 'brokenlink';
			$wpdb->insert( 
				$table_name, 
				array( 
					'time' => $time,
					'knox_id' => $knox_id,
					'email' => $email,
					'full_name' => $full_name,
					'employee_number' => $employee_number,
					'department_name' => $department_name,
					'user_information' => $user_information,
					'target_url' => $target_url,
					'total_number' => $total_count,
					'broken_number' => $broken_count,
					'result_url' => $filepath,
				)
			);

			$headers = array('Content-Type: text/html; charset=UTF-8');
			$subject = 'Broken Link Checker Result';
			$attachments = array(getcwd()."/result/".$filename.".log", getcwd()."/result/".$filename.".csv");
			global $msg_body;
			// echo $msg_body;
			wp_mail($email, $subject, $msg_body, $headers, $attachments);
			#$wpdb->show_errors();
			#print($wpdb->last_result);
			#$wpdb->print_error();
			#var_dump($wpdb);
		}
		// if the form is submitted but the name is empty
		if ( isset( $_POST["submit_form"] ) && $_POST["target_url"] == "" ) {
			$html .= "<p>You need to fill the required fields.</p>";
		}
		// outputs everything
		echo $html;
	}
	else {
		$login = '<meta http-equiv="refresh" content="0; url='.wp_login_url( get_permalink() ).'">';
		echo $login;
	}
}

function print_wp($msg){
	global $msg_body;
	echo nl2br($msg);
	$msg_body.=$msg."<br>";
}

function save_sessions() {
	$pluginpath = plugin_dir_path(__FILE__);
	// $command = "sudo python3.5 ".$pluginpath."python-scripts/file-creation.py";
	$command = '/usr/bin/python3.5 '.$pluginpath.'python-scripts/saveSSSession.py';
	
	#echo $command;
	$descriptorspec = array(
		0 => array("pipe", "r"),
		1 => array("pipe", "w"),
		2 => array("file", "./result/error-output-cron.log", "w"),
	);

	$env = array(
		'LANG' => 'en_US.utf-8',
		'db_user' => DB_USER,
		'db_password' => DB_PASSWORD,
		'secret_key' => DB_SECRET_KEY,
		'db_name' => DB_NAME
	);
	
	$process = proc_open($command, $descriptorspec, $pipes, NULL, $env);
	if (is_resource($process)) {
		fwrite($pipes[0]);
		$current = "";
		while(!feof($pipes[1])) {
			$message = fgets($pipes[1], 1024);
			$current.=$message;
		}
		fclose($pipes[1]);
		file_put_contents (getcwd()."/result/save-session.log" , $current);
		$return_value = proc_close($process);
		$message = "[END] Command returned $return_value";
	}
}

function my_cron_schedules($schedules) {
    if(!isset($schedules["15min"])){
        $schedules["15min"] = array(
            'interval' => 15*60,
            'display' => __('Once every 15 minutes'));
    }
    if(!isset($schedules["30min"])){
        $schedules["30min"] = array(
            'interval' => 30*60,
            'display' => __('Once every 30 minutes'));
	}
	if(!isset($schedules["1day"])){
        $schedules["1day"] = array(
            'interval' => 24*60*60,
            'display' => __('Once every day'));
    }
    return $schedules;
}
add_filter('cron_schedules','my_cron_schedules');
if (!wp_next_scheduled('save_sessions_hook')) {
	wp_schedule_event( strtotime("2018-12-20 15:01:00"), 'daily', 'save_sessions_hook' );
}

add_action ( 'save_sessions_hook', 'save_sessions' );
?>
