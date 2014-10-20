#!/usr/bin/perl -wT
# -------------------------------------------------------------------          
# Yet Another Guestbook, a simple guestbook program for the WWW
# Copyright (C) 1996-2005 by James A. Chappell (rlrrlrll@gmail.com)
#                                                                      
# Yet Another Guestbook is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation; either version 2, or (at your option) any 
# later version.                                                        
#                                                                        
# Yet Another Guestbook is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of  
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU     
# General Public License for more details.                              
#                                                                        
# You should have received a copy of the GNU General Public License     
# along with Guestbook; see the file COPYING.  If not, write to the Free
# Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.          
# -------------------------------------------------------------------
#                                                                        
# Yet Another Guestbook: Version 2.1
# Created by James A. Chappell
# Created: 21 October 1996
# Last Modified:  02 March 2005
# History:
# 21-oct-1996	created
# 18-may-2000   update email, remove count, bracket entry with table stuff
# 27-jun-2000   add location
# 14-nov-2000   added email notify
# 15-nov-2000   allow "GET" method (not tested)
# 20-nov-2000   use associative array for name/data pairs
# 22-nov-2000   added command line option (-d) to display guestbook
# 30-nov-2000   use strict
# 01-dec-2000   use CGI
# 11-dec-2000   change (hopefully improve) display option
# 07-jan-2002   use Mail::Mailer
# 19-feb-2002   1.0 release
# 10-nov-2002   Fixed minor file locking issues
# 22-nov-2003   Attempt to hide email addresses from spam bots
# 27-nov-2003   Tweak email obfuscation
# 02-mar-2005   add rel="nofollow" to user created links
#--------------------------------------------------------------------

use strict ;
use Fcntl ':flock' ; # import LOCK_* constants
use Getopt::Std ;
use Mail::Mailer ;
use CGI ;

#--------------------------------------------------------------------
#
# Path to guestbook.cgi (this file)
#
# guestbook.cgi needs to be in your cgi-bin directory.  You will
# probably want to consult with your isp on how to set up
# cgi scripts.
#
# Modify guestbook.cgi as per the instructions in these comments.
# 
#--------------------------------------------------------------------
#
# $GB_PATH, $GUEST_BOOK, and $HOME_PAGE, must be changed to
# the appropriate values.
#
# Path to the guestbook file
#
# Replace /u/sh/username/www/guestbook.txt with the path to your guestbook file 
#
my $GB_PATH = "/u/sh/username/www/guestbook.txt" ;
#
# Replace www.your_isp.com/~username/guestbook.html with the URL for
# your guestbook
#
my $GUEST_BOOK = "<p><a href=http://www.your_isp.com/~username/guestbook.html>View Guestbook</a></p>" ;
#
# Replace www.your_isp.com/~username with the URL for you home page
#
my $HOME_PAGE = "<p><a href=http://www.your_isp.com/~username>Go to my Homepage</a></p>" ;
#
#--------------------------------------------------------------------
#
# Modifying the following is optional
#
# Define home page and guestbook URLs
#
#
# Title
#
my $TITLE = "Thank You" ;
#
# HTML Header
#
my $HEADER = "" ;
my $MESSAGE = "<H1>Thank you</H1><hr>" ;
my $FOOTER = "" ;
#
# Address to wich email notifications are sent
#
# Set $GBADMIN to the address you
# want notifications to be sent. Leave blank
# if you don't want notifications to be sent
#
my $GBADMIN = "" ;

# Set NOFOLLOW = 0 if you don't want rel="nofollow" added to links
#
my $NOFOLLOW = 1 ;
#
#
# The "name" part of name/value pairs.  The quoted text
# corresponds to the "input name" in the HTML form.
#
my $GB_NAME = 'name' ;
my $GB_EMAIL = 'email' ;
my $GB_HOMEPAGE = 'homepage' ;
my $GB_LOCATION = 'location' ;
my $GB_REFER = 'reference' ;
my $GB_COMMENT = 'comments' ;
#
# Format strings for the guestbook entries
#
my $GUEST_NAME = "<strong>Name:</strong> %s<br>" ;
my $GUEST_DATE = "<strong>Date:</strong> %s<br>" ;
my $GUEST_MAIL = "<strong>Email:</strong> <a href=mailto:%s>%s</a><br>" ;
my $GUEST_MAIL_ALT = "<strong>Email:</strong> %s<br>" ;
my $GUEST_PAGE = "<strong>Homepage:</strong> <a href=\"%s\">%s</a><br>" ;
my $GUEST_PAGE_ALT = "<strong>Homepage:</strong> %s<br>" ;
my $GUEST_LOCATION = "<strong>From:</strong> %s<br>" ;
my $GUEST_REFER = "<strong>Referred from:</strong> %s<br>" ;
my $GUEST_COMMENT = "<strong>Comments:</strong> " ;
#
#--------------------------------------------------------------------
#
# No further modifications are required from here on
#
#--------------------------------------------------------------------
#
sub nofollow
{
  my $str = shift ;
  $str =~ s#<a\s([^>]*\s*href\s*=[^>]*)>#
    my @attr = $1 =~ /[^=[:space:]]*\s*=\s*"[^"]*"|[^=[:space:]]*\s*=\s*'[^']*'|[^=[:space:]]*\s*=[^[:space:]]*/g;
    my @rel = grep { /^rel\s*=/i } @attr;
    my $rel;
    $rel = pop @rel if @rel;
    if ($rel)
    {
      $rel =~ s/^(rel\s*=\s*['"]?)/$1nofollow /i;
    }
    else
    {
      $rel = 'rel="nofollow"';
    }
    @attr = grep { !/^rel\s*=/i } @attr;
        '<a ' . (join ' ', @attr) . ' ' . $rel . '>';
  #xieg;
  $str;
}


#
# Attempt to foil spam bots by burying email address in a
# bunch of javascript
#
sub print_line
{
    my $line = shift ;

    if ($NOFOLLOW)
    {
        $line = nofollow($line) ;
    }
    my $idx1 = index($line, "<strong>Email:</strong> <a href=mailto:") ;
    if ($idx1 < 0)
    {
        print $_ ;
        return ;
    }

    my $len = length($line) ;
    my $idx2 = index($line, "</a>") ;
    my $line1 = substr($line, 0, $idx1) ;
    my $line2 = substr($line, $idx2 + 4, $len - ($idx2 + 4)) ;
    my $email = substr($line, $idx1 + 39, $idx2 - $idx1 - 39) ;

    ($email, my $jnk) = split('>', $email) ;

    (my $name, my $dom) = split('\@', $email) ;
    my @doms = split('\.', $dom) ;

    print "$line1\n" ;
    print "<script type=\"text/javascript\" language=\"javascript\">\n" ;
    print "<!--\n" ;
    print "document.write('<strong>Email:<\\/strong> <a href=\"'" ;
    print "+ String.fromCharCode(109,97,105,108,116,111,58) + '$name' + String.fromCharCode(64)" ;
    for (my $i = 0 ; $i <= $#doms ; $i++)
    {
        print " + '$doms[$i]'" ;
        if ($i < $#doms)
        {
            print " + String.fromCharCode(46)" ;
        }
    }
    print " + '\">'" ;
    print " + '$name'" ;

    print "+ '<\\/a>') ;" ;
    print "\n// -->\n" ;
    print "<\/script>\n" ;
    
    print "$line2" ;
}


my $q = new CGI ;

use vars qw($opt_d);
getopts("d") ;

print $q->header("text/html");

if ($opt_d)
{
    open (GB, "$GB_PATH") || die "Sorry, couldn't open $GB_PATH\n";
    flock(GB, LOCK_SH) ;

    my @data = reverse(<GB>) ;

    close (GB);

    foreach(@data)
    {
        print_line($_) ;
    }
}
else
{
    my $name = $q->param($GB_NAME) ;
    my $email = $q->param($GB_EMAIL) ;
    my $homepage = $q->param($GB_HOMEPAGE) ;
    my $location = $q->param($GB_LOCATION) ;
    my $refer = $q->param($GB_REFER) ;
    my $comment = $q->param($GB_COMMENT) ;
#
#   Open the guestbook file
#
    open(GB, ">>$GB_PATH") || die "Cannot open $GB_PATH\n" ;
    flock(GB, LOCK_EX) ;
    seek(GB, 0, 2) ;
#
#   Save the entry in the guest book
#
    printf(GB "<table border=\"0\"><tr><td>") ;
    printf(GB $GUEST_NAME, $name) ;
    if (index($email, "@") > 0)
    {
        printf(GB $GUEST_MAIL, $email, $email) ;
    }
    else
    {
        printf(GB $GUEST_MAIL_ALT, $email) ;
    }

    my $s_tod = time ;
    my $tod = localtime($s_tod) ;

    printf(GB $GUEST_DATE, $tod) ;
    if (index($homepage, "://") > 0)
    {
        printf(GB $GUEST_PAGE, $homepage, $homepage) ;
    }
    else
    {
        printf(GB $GUEST_PAGE_ALT, $homepage) ;
    }
    printf(GB $GUEST_LOCATION, $location) ;
    printf(GB $GUEST_REFER, $refer) ;

    print GB  "$GUEST_COMMENT<br>" ;
#
#   Replace carrige returns with the <br> HTML tag - Note that some systems
#   use carriage return line feed combos, hence the mess below
# 
    $comment =~ s/\cM\n/<br>/g ;
    $comment =~ s/\n/<br>/g ;
#
#   print the comment
#
    print GB  "$comment<br><br>" ;
    printf(GB "</td></tr></table><hr><br>\n") ;

    close GB ;
#
#   Send Email notification
#
    if ($GBADMIN)
    {
        my $mailer = new Mail::Mailer("sendmail") ;
        my $remote_addr = $q->remote_addr ;
        $mailer->open(
            {
                To      => $GBADMIN,
                From    => $GBADMIN,
                Subject => "Subject: Guestbook has been signed ($tod)"
            }
        ) ;
        print $mailer "Name:   $name <$email>\nRemote-IP: $remote_addr\n" ;
        close $mailer ;
    }
#
#   Print a thank you message and links to the guestbook and home page
#
    print $q->start_html(-title => $TITLE) ;

    print "$HEADER\n" ;
                                                                         
    print "$MESSAGE\n" ;
    print "$GUEST_BOOK\n" ;
    print "$HOME_PAGE\n" ;

    print "$FOOTER\n" ;

    print $q->end_html ;
}
